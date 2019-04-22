#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
from packages import Util, proxies




sys.__APP_LOG__ = False

import pymongo
import pika
import re
import time
import math
from threading import Thread
from multiprocessing import Process

try:
    import json
except ImportError:
    import simplejson as json

try:
    import argparse
except ImportError:
    print('没有发现 argparse 模块，对于python版本小于2.7的请安装 argparse 模块!')
    sys.exit(0)

from config import *
from packages.daemon import Daemon

from packages.proxies import *
import requests
from packages.rabbitmq import RabbitMQ

# 一分钟或者几分钟更新的站点
_PROXY_SITE_MINUTE = ('kuaidaili', 'didsoft', 'p76lt')

LOGFILE = 'proxies_' + datetime.datetime.now().strftime("%Y-%m-%d_%H") + ".log"
_handler = RotatingFileHandler(filename=os.path.join(LOGDIR, LOGFILE), mode='a+')
_handler.setFormatter(logging.Formatter(fmt='>>> %(asctime)-10s %(name)-12s %(levelname)-8s %(message)s',
                                        datefmt='%H:%M:%S'))
_logger = logging.getLogger('proxies')
_logger.setLevel(level)
_logger.addHandler(_handler)


def check_proxy(ip, data_list=[], error=0):
    '''
    检测代理
    '''
    headers = {
        'user_agent': 'HQchip Robot',
    }

    timeout = 15
    if 'socks' not in ip:
        proxy = {'http': 'http://' + ip}
    else:
        proxy = {'http': ip}
    # 检测是否可用和是否是高匿带代理，返回{"statue":1}是高匿代理
    print('Check IP : %s' % ip)

    res = proxies.fetch('http://proxy.elecfans.net/', headers=headers, proxies=proxy,
                        timeout=timeout, hide_print=True)
    try:
        if res:
            data = json.loads(res)
            status = int(data['statue'])
        else:
            status = None
    except Exception as e:
        # _logger.exception('检测异常')
        status = None
    data_list.append((ip, status, error))
    return status


_re_letter = None


def check_proxy_ip(ip):
    '''
    检测代理IP
    对于没有端口或者端口

    :param ip:
    :return:
    '''
    global _re_letter
    if not ip:
        return False
    try:
        _proxy_scheme, _proxy_host, _proxy_port = Util.get_host(ip)
    except:
        return False
    if _re_letter is None:
        _re_letter = re.compile('[^0-9]+')
    if not _proxy_port or _re_letter.search(str(_proxy_port)):
        return False
    if not _proxy_host:
        return False
    _host = _proxy_host.split('.')[-1]
    if _re_letter.search(_host) and _host not in ('com', 'net', 'cn', 'org', 'us', 'jp', 'tw', 'me'):
        return False
    return True


class HQchipProxyIp(object):
    '''
    hqchip 代理IP检测及获取
    '''

    def __init__(self, action=None, proxy_threshold=50):
        if not action or action not in ('fetch', 'check', 'delete'):
            print('无效操作')
            return

        if not self.connect_mongo(service=1):
            return
        getattr(self, '%s_proxy' % action)(proxy_threshold=proxy_threshold)
        self.close_mongo(service=1)

    def fetch_proxy(self, **kwargs):
        '''
        获取代理
        '''
        global _PROXY_SITE_MINUTE
        last_fetch_time = Util.number_format(Util.file('proxies/last_fetch_time'), 0)
        unix_time = int(time.time())
        _fetch_all_proxies = False
        collect = self.mongo_db_s1['iplist']
        # 每4个小时完整获取一次
        if (unix_time - last_fetch_time) > DATA_CACHE_TIME / 12:
            _fetch_all_proxies = True
            # iplist数据每2天清空一次
            if last_fetch_time > 0 and (unix_time - last_fetch_time) > DATA_CACHE_TIME / 2:
                collect.remove({}, muti=True)

        if _fetch_all_proxies:
            Util.file('proxies/last_fetch_time', int(time.time()))
        total = 0
        for p in proxies.__all__:
            if not _fetch_all_proxies and p not in _PROXY_SITE_MINUTE:
                continue
            module = globals().get(p, None)
            if module is None:
                continue
            try:
                timeout = module.__timeout__
            except:
                timeout = 0
            for url in module.__url__:
                iplist = getattr(module, 'fetch_proxy_data')(url)
                if not iplist:
                    iplist = set()
                count = len(iplist)
                total += count
                print('Site: %s ; 共获取 %s 个代理IP' % (url, count))
                for ip in iplist:
                    if not check_proxy_ip(ip):
                        print('代理IP: %s 无效已被丢弃' % ip)
                        continue
                    try:
                        collect.insert({'ip': ip, 'error': 0})
                    except pymongo.errors.DuplicateKeyError:
                        pass
                    except:
                        _logger.exception('STATSUS:-206; INFO: 代理检测异常')
                if timeout > 0:
                    print('---------- sleep %s s -----------' % timeout)
                    time.sleep(timeout)
        print('抓取完毕，共获取 %s 个代理IP' % total)

    def check_proxy(self, **kwargs):
        '''
        检测代理

        iplist -> proxys
        '''
        queue_list = self.get_queue_list(queue_name=PROXY_QUEUE)
        if not queue_list:
            self.check_publish_proxy(queue_name=PROXY_QUEUE)
            return
        total_count = len(queue_list)
        print('共获取 %s 个代理IP等待验证' % total_count)
        valid_num = 0
        threads = []
        data_list = []
        for proxy in queue_list:
            if 'ip' not in proxy:
                continue
            t = Thread(target=check_proxy, args=(proxy['ip'], data_list, proxy.get('error', 0)))
            threads.append(t)
            t.start()
            time.sleep(0.01)
        for t in threads:
            # print t.getName(),time.time()
            if t.isAlive():
                t.join(15)

        collect = self.mongo_db_s1['proxys']
        iplist = None
        for data in data_list:
            if not isinstance(data, (tuple, list)):
                continue
            if data[1] is not None:
                print('IP：%s 验证有效' % data[0])

                try:
                    collect.insert({'ip': data[0], 'anonymous': data[1]})
                except pymongo.errors.DuplicateKeyError:
                    collect.update({'ip': data[0]}, {"$set": {'anonymous': data[1]}})
                except Exception as e:
                    _logger.exception('检测代理更新或写入mongodb异常')
                    continue
                valid_num += 1
            else:
                print('IP：%s 无效已被丢弃' % data[0])
                if iplist is None:
                    iplist = self.mongo_db_s1['iplist']
                try:
                    iplist.update({'ip': data[0]}, {"$set": {'error': data[2] + 1}})
                except:
                    _logger.exception('检测代理更新mongodb异常')
        print('验证结束，共有 %s 个有效IP，有效率：%.2f %%' % (valid_num, valid_num / float(total_count) * 100))

    def delete_proxy(self, **kwargs):
        '''
        删除无效代理

        check proxys
        :return:
        '''
        proxy_threshold = kwargs.get('proxy_threshold', 50)
        collect = self.mongo_db_s1['proxys']
        count = collect.find().count()
        # 保证proxys中至少有 [proxy_threshold 默认 50] 个代理，低于时 delete 进程也会自动更换成 check
        if count < proxy_threshold:
            print('proxys 数量不足，检测 iplist 获取代理中')
            self.check_proxy()
            return
        print('共获取 %s 个代理IP等待验证' % count)

        valid_num = 0
        ip_list = []
        proxy_list = collect.find()
        ip_list = []
        count = 0
        for proxy in proxy_list:
            # 数据不完整或者连续超过3次检测无效的代理直接删除
            if 'ip' not in proxy:
                try:
                    collect.remove({'_id': proxy['_id']})
                except Exception as e:
                    _logger.exception('检测代理异常')
                continue
            count += 1
            ip_list.append(proxy['ip'])

        # 每次50个线程进行检测
        num = int(math.ceil(float(count) / 50.0))
        for i in range(num):
            threads = []
            data_list = []
            start = i
            end = 50
            for ip in ip_list[start:end]:
                t = Thread(target=check_proxy, args=(ip, data_list))
                threads.append(t)
                t.start()
                time.sleep(0.01)
            # 清理内存
            del ip_list[start:end]
            for t in threads:
                # print t.getName(),time.time()
                if t.isAlive():
                    t.join(15)

            iplist = None
            for data in data_list:
                if not isinstance(data, (tuple, list)):
                    continue
                if data[1] is not None:
                    print('IP：%s 验证有效' % data[0])

                    try:
                        collect.update({'ip': data[0]}, {"$set": {'anonymous': data[1]}})
                        valid_num += 1
                    except:
                        _logger.exception('更新代理异常')
                else:
                    print('IP：%s 无效已被删除' % data[0])

                    collect.remove({'ip': data[0]})
                    if iplist is None:
                        iplist = self.mongo_db_s1['iplist']
                    try:
                        iplist.update({'ip': data[0]}, {"$inc": {'error': 1}})
                    except:
                        _logger.exception('检测代理更新mongodb异常')

        print('验证结束，共有 %s 个有效IP，有效率：%s %%' % (valid_num, float(valid_num) / float(count) * 100))

    def connect_mongo(self, service=0, num=0):
        '''
        连接mongodb

        @param service      mogodb服务器组号
        @param num          重试次数

        '''
        try:
            conn = pymongo.MongoClient(DATABASES['mongo'][service])
            db = conn.get_default_database()
            if service == 0:
                self.__setattr__('mongo_conn', conn)
                self.__setattr__('mongo_db', db)
            else:
                self.__setattr__('mongo_conn_s%s' % service, conn)
                self.__setattr__('mongo_db_s%s' % service, db)
            return True
        except Exception as e:
            num += 1
            print(type(e))
            print('连接mongodb异常，异常信息：%s' % e)
            print('正在重试连接，终止请按 Ctrl + c')
            if num == 3:
                print('系统已进行3次重试连接操作，请根据异常信息检查配置')
                return False
            self.connect_mongo(service=service, num=num)

    def get_queue_list(self, queue_name=None, queue_count=QUEUE_LIMIT):
        '''
        获取队列列表
        '''
        if not queue_name:
            return None
        queue_list = []
        try:
            connection = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)

            def callback(ch, method, properties, body):
                queue_list.append(json.loads(body))
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=queue_count)  # 单次拿去数量
            channel.basic_consume(callback, queue=queue_name)
            connection.close()
            return queue_list
        except Exception as  e:
            print(e)

            return None

    def put_queue_list(self, message_list, queue_name=None):
        '''
        提交异常至队列列表
        '''
        if not queue_name:
            return
        try:
            if not message_list:
                return
            if isinstance(message_list, dict):
                message_list = [message_list]
            connection = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            for message in message_list:
                if queue_name == PROXY_QUEUE:
                    print('IP : %s 数据已提交至抓取代理待处理队列' % message.get('ip', ''))

                if 'error' not in message:
                    message['error'] = 0
                if message['error'] >= 5:
                    # 超过5次异常
                    _logger.exception('STATUS:605 ; INFO:超过5次异常，请检查 ; DATA:%s' % message)
                    continue
                message = json.dumps(message)
                channel.basic_publish(exchange='',
                                      routing_key=queue_name,
                                      body=message,
                                      properties=pika.BasicProperties(
                                          delivery_mode=2,  # 持久化
                                      ))
            connection.close()
        except Exception as e:
            print(e)

            return None

    def get_queue_info(self, queue_name=None):
        '''
        获取队列信息
        '''
        queue_info = {'memory': 0, 'messages': 0, 'messages_ready': 0, 'messages_unacknowledged': 0}
        try:
            api = 'http://%s:15672/api/queues/' % QUEUE_HOST
            rs = requests.get(api, auth=requests.auth.HTTPBasicAuth('guest', 'guest'))
            data_list = json.loads(rs.text)
        except Exception as e:
            print(e)

            return queue_info
        try:
            for data in data_list:
                if data['name'] == queue_name:
                    return {
                        'memory': data['memory'],
                        'messages': data['messages'],
                        'messages_ready': data['messages_ready'],
                        'messages_unacknowledged': data['messages_unacknowledged'],
                    }
        except Exception as e:
            print(e)
        print(queue_info)

    def check_publish_proxy(self, queue_name=None, min_num=0):
        '''
        检测提交代理ip至队列
        :return:
        '''
        qsize = RabbitMQ(name=queue_name, dsn=AMQP_URL).qsize()
        if qsize > min_num:
            return
        collect = self.mongo_db_s1['iplist']
        total_count = collect.find().count()
        print('iplist 中共获取 %s 个代理IP等待验证' % total_count)

        ip_list = []
        proxy_list = collect.find()
        for proxy in proxy_list:
            # 数据不完整或者连续超过5次检测无效的代理直接删除
            _error = proxy.get('error', 0)
            if 'ip' not in proxy or _error >= 5:
                try:
                    collect.remove({'_id': proxy['_id']})
                except:
                    _logger.exception('检测代理异常')
                continue
            ip_list.append({'ip': proxy['ip'], 'error': _error})
            if len(ip_list) >= 100:
                self.put_queue_list(ip_list, queue_name=queue_name)
                ip_list = []
        self.put_queue_list(ip_list, queue_name=queue_name)

    def close_mongo(self, service=0):
        try:
            if service == 0:
                self.mongo_conn.close()
            else:
                getattr(self, 'mongo_conn_s%s' % service).close()
        except:
            pass


class HQchipProxyIpDaemon(Daemon):
    '''
    守护进程运行模式
    '''

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', **kwargs):
        self.action = kwargs.get('action', None)
        if self.action not in ('check', 'delete', 'fetch'):
            print('指定操作无效')

            sys.exit(-1)
        self.sleep_time = kwargs.get('sleep_time', 60)
        self.proxy_threshold = kwargs.get('proxy_threshold', 50)
        super(HQchipProxyIpDaemon, self).__init__(pidfile, stdin=stdin, stdout=stdout, stderr=stderr)

    def run(self):
        while True:
            HQchipProxyIp(action=self.action, proxy_threshold=self.proxy_threshold)
            time.sleep(self.sleep_time)


def run(action=None, sleep_time=60, **kwargs):
    if not action:
        return
    while True:
        try:
            HQchipProxyIp(action=action, **kwargs)
            print('------ sleep %s sec -------' % sleep_time)

            time.sleep(sleep_time)
        except KeyboardInterrupt:
            break


def main():
    parser = argparse.ArgumentParser(description=u"华强芯城代理IP获取及检测", add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息', action='store_true', default=False)
    parser.add_argument('-c', '--check', dest='action', help=u'检测 iplist 中的代理并将有效代理保存至 proxys 中',
                        action='append_const', const='check')
    parser.add_argument('-d', '--delete', dest='action', help=u'删除proxys中验证无效的代理',
                        action='append_const', const='delete')
    parser.add_argument('-f', '--fetch', dest='action', help=u'获取新的代理数据记录至 iplist',
                        action='append_const', const='fetch')
    parser.add_argument('-t', '--sleep-time', help=u'指定暂停时间(默认5s，如果选择为fetch 默认为 1h)',
                        default=5, type=int)
    parser.add_argument('-p', '--pid', dest='pid', help=u'指定运行的进程pid文件（仅守护进程运行模式有效）')
    parser.add_argument('--daemon', dest='daemon', help=u'以守护进程服务模式运行，start启动服务，stop停止服务，'
                                                        u'restart重启服务', choices=['start', 'stop', 'restart'])
    parser.add_argument('--proxy-threshold', help=u'代理最小阀值，仅适用于于删除无效代理时，'
                                                  u'当小于此数目会暂停删除转为检测，默认为50', type=int, default=50)
    # parser.add_argument('--work',help = u'work进程数量，默认为1',type=int,default=1)
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        print("\n示例")
        print(' 抓取代理数据, t为一次抓取后暂停时间默认为1h    %s -f -t 3600' % sys.argv[0])
        print(' 检测代理数据，将iplist中有效数据移至proxys     %s -c -t 30' % sys.argv[0])
        print(' 删除proxys中无效的代理IP                       %s -d -t 30' % sys.argv[0])
        print(' 同时运行抓取、检测、删除代理IP                 %s -fcd -t 30' % sys.argv[0])
        print(' 以守护进程模式运行                             %s -fcd -t 30 --daemon start' % sys.argv[0])
        print(" 以守护进程模式运行如需开启多个进程，需要使用pid选项 \n" \
              '                      %s -fcd -t 30 --pid=/var/run/hqchip-proxy-30.pid --daemon start' % sys.argv[0])
        print()
    elif args.action:
        if args.daemon:
            for action in args.action:
                pidfile = '/var/run/hqchip-proxy-%s.pid' % action if not args.pid else args.pid
                if action == 'fetch' and args.sleep_time < 60:
                    sleep_time = 3600
                else:
                    sleep_time = args.sleep_time
                ps = HQchipProxyIpDaemon(pidfile, action=action, sleep_time=args.sleep_time,
                                         proxy_threshold=args.proxy_threshold)
                getattr(ps, args.daemon)()
        else:
            if len(args.action) == 1:
                action = args.action[0]
                proxy_threshold = args.proxy_threshold
                sleep_time = args.sleep_time
                if action == 'fetch' and sleep_time < 60:
                    sleep_time = 3600
                del args
                run(action=action, sleep_time=sleep_time, proxy_threshold=proxy_threshold)
            else:
                plist = []
                for action in args.action:
                    if action == 'fetch' and args.sleep_time < 60:
                        sleep_time = 3600
                    else:
                        sleep_time = args.sleep_time
                    p = Process(target=run, args=(action, sleep_time), kwargs={
                        'proxy_threshold': args.proxy_threshold
                    })
                    p.start()
                    plist.append(p)

                for p in plist:
                    p.join()

    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
