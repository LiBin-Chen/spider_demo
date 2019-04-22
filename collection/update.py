#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# 


import sys
import copy
import time
import random
import argparse
import threading
import multiprocessing

try:
    import json
except ImportError:
    import simplejson as json
import requests
import config
from packages import rabbitmq
from packages import Util as util
from packages import supplier

# global object
mq = rabbitmq.RabbitMQ()


class UpdateChip(object):
    """更新元器件"""

    def __init__(self, **kwargs):
        self._init_args(**kwargs)
        self.run()

    def _init_args(self, **kwargs):
        """初始化参数"""
        # self.action = kwargs.get('action', 'put')
        self.no_proxy = kwargs.get('no_proxy')
        self.queues = kwargs.get('queues')  # 获取队列
        self.exception_threshold = kwargs.get('exception_threshold', 5)
        self.notice_threshold = kwargs.get('notice_threshold', 30)
        self.notice = kwargs.get('notice')
        self.limit = kwargs.get('limit', config.QUEUE_LIMIT)
        self.pay = kwargs.get('pay', False)
        self.use = kwargs.get('use', False)
        self.suppliers = kwargs.get('supplier', [])
        self.optype = kwargs.get('optype')
        if self.optype == 'hot':
            self._supp_dict = {}
            for k in config.DB_KEY:
                self._supp_dict[config.DB_KEY[k]] = k
            self._max_depth = kwargs.get('max_depth', 10)

    def run(self):
        """运行"""
        qnum = len(self.queues)
        handler = getattr(self, 'update_data')  # 更新数据
        if qnum > 1:
            plist = []
            for qname in self.queues:
                p = multiprocessing.Process(target=handler, args=(qname,))
                plist.append(p)
                p.start()
            for p in plist:
                p.join()
        else:
            handler(self.queues[0])

    def update_data(self, queue_name=None):
        """更新指定队列数据"""
        if not queue_name:
            return 0
        # queue_name = 'default_goods_queue'
        qsize = mq.qsize(queue_name)
        self.limit = 10
        self.limit = self.limit if qsize > self.limit else qsize  # 每次更新的数量
        queue_list = []
        for i in range(self.limit):
            queue_data = mq.get(queue_name)
            queue_list.append(queue_data)

        if not queue_list:
            print('等待中，队列 %s 为空' % queue_name)
            return 0
        proxy = None
        # if not self.no_proxy:
        if 0:
            proxy = self.get_prolist()
        tlist = []
        data_list = []
        total_num = 0

        for data in queue_list:
            # 无效队列数据
            if 'id' not in data:
                continue
            if 'proxy' in data:
                del data['proxy']
            # 有效队列的总数（非型号总数）
            total_num += 1
            t = threading.Thread(target=self.fetch_update_data,
                                 args=(data_list, proxy), kwargs=data)
            tlist.append(t)
            t.start()
            time.sleep(0.1)

        try:
            for t in tlist:
                t.join(45)
        except (KeyboardInterrupt, SystemExit):
            mq.put(queue_name, queue_data)
            return 0
        del data, queue_list

        valid_num = 0
        delete_list = []

        # 所有线程执行完毕后 再进行数据处理
        # print('data_list', data_list)
        for data in data_list:
            if not data:
                print('data----: ', data)
                continue
            if data['status'] == 200:
                mq.put(config.WAIT_UPDATE_QUEUE, data['dlist'])  # 等待提交数据
                valid_num += 1
                id = data.get('dlist').get('id', )
                lottery_name = data.get('dlist').get('lottery_name', )
                status = data.get('status')
                config.LOG.info('ID：{0} ;彩种: {1} ;数据获取成功：{2} ;提交到入库队列:  {3} !'.format(id, lottery_name, status,
                                                                                      config.WAIT_UPDATE_QUEUE))
                continue
            else:
                delete_list.append(data)

            count = data.get('count', '')
            if count and count < self.exception_threshold:  # 重复更新的次数
                config.LOG.info('ID：%s，更新状态：%s, 重新入队中!' % (data.get('id', ), data['status']))
                # update_list.append(data)
                mq.put(queue_name, data)
            else:
                config.LOG.error('ID：%s，更新状态：%s, 重试次数超过阀值,保存日志中!' % (data.get('id', ), data['status']))
                if 'count' in data:
                    del data['count']
                if 'time' not in data:
                    data['time'] = util.date()
                # db.mongo['update_exception_logs'].insert(data)
                mq.put('update_exception_logs', data)

        self.write_update_info(valid_num)
        print('队列 %s 本次共有 %s 条数据更新成功，成功率：%s %%' %
              (queue_name, valid_num, valid_num * 1.0 / total_num * 100 if total_num > 0 else 0))
        print('完成 , 等待下一个队列!')
        print('*' * 50)

    def write_update_info(self, num_list):
        '''记录更新信息

        @param num_list     记录每次更新数目信息
        @param name         记录类型值，默认count为成功值
        '''
        if not num_list:
            return None
        # mq.put('crawler_update_stats', {'data': num_list, 'time': util.unixtime()})
        mq.put('crawler_update_stats', {'data': num_list, 'time': util.date()})

    def fetch_update_data(self, data_list=[], proxy=None, **kwargs):
        '''获取更新数据

        @return
            无论请求data_list
                0       为空（无视）
                -401      错误（需要重试，程序出错，语法或者由于异常删除造成错误，需要检查程序）
                -402      数据异常（需要重试，需要检验数据获取情况）
                -400    代理异常（须重试，可以无视）
                -200    非200状态，代理异常或者数据异常（须重试，特别注意此种情况是否进入死循环）
                200     正常状态，并非指http状态码
                404     产品不存在已被删除

        '''
        # 根据url进行网站判断, 进而调用网站爬虫的模块

        update_url = kwargs.get('update_url', '')
        if not update_url:
            return
        supplier_name = update_url.split('.')[1]
        if supplier_name is None:
            return None
        headers = {
            'user-agent': random.choice(config.USER_AGENT_LIST),
        }
        if 'cjcp' in update_url:
            return None
        try:
            if not hasattr(supplier, supplier_name):
                module_name = 'supplier.{0}'.format(supplier_name)
                if module_name not in sys.modules:
                    __import__(module_name)
                obj = sys.modules[module_name]
            else:
                obj = getattr(supplier, supplier_name)
            if 'fetch_update_data' in dir(obj):
                _fetch_update_data = getattr(obj, 'fetch_update_data')
            else:
                kwargs['status'] = -401
                data_list.append(kwargs)
                return None
        except Exception as e:
            config.LOG.exception('STATUS: -401, ID: {0} 导入错误,将进行重试: {1}'.format(kwargs['id'], e))
            kwargs['status'] = -401
            data_list.append(kwargs)
            return None
        try:
            kwargs['headers'] = headers
            kwargs['proxy'] = proxy
            data_list.append(_fetch_update_data(**kwargs))
        except Exception as e:
            kwargs['status'] = -402
            if 'headers' in kwargs:
                del kwargs['headers']
            if 'proxy' in kwargs:
                del kwargs['proxy']
            data_list.append(kwargs)
            config.LOG.exception('STATUS: -402, ID: %(id)s', {'id': util.u2b(kwargs['id'])})

    def fetch_search_data(self, data_list=[], err_list=[], proxy=None, supp=None, **kwargs):
        """根据搜索关键词获取产品产品数据（可能为url也可能为详细信息）"""
        if not supp or 'keyword' not in kwargs:
            return None
        headers = {
            'user-agent': random.choice(config.USER_AGENT_LIST),
        }
        keyword = util.u2b(kwargs['keyword'])
        supplier_name = config.DB_KEY[supp]
        try:
            if not hasattr(supplier, supplier_name):
                module_name = 'supplier.{0}'.format(supplier_name)
                if module_name not in sys.modules:
                    __import__(module_name)
                obj = sys.modules[module_name]
            else:
                obj = getattr(supplier, supplier_name)
            if hasattr(obj, 'api_search_data'):
                _fetch_function = getattr(obj, 'api_search_data')
            else:
                _fetch_function = getattr(obj, 'fetch_search_data')
        except Exception as e:
            config.LOG.exception('STATUS: -401, Keyword: %(keyword)s', {'keyword': keyword})
            if kwargs.get('count', 1) < self.exception_threshold:
                kwargs['status'] = -401
                kwargs['count'] = kwargs.get('count', 1) + 1
                err_list.append(kwargs)
            return None
        data_dict = {
            'detail': [],
            'list': [],
            'url': []
        }
        if self.optype == 'hot' and self.use:
            kwargs['hot_search'] = True
        del kwargs['keyword']
        try:
            _fetch_function(keyword, supp, data_dict, headers, **kwargs)
        except Exception as e:
            config.LOG.exception('STATUS: -402, Keyword: %(keyword)s', {'keyword': keyword})
            if kwargs.get('count', 1) < self.exception_threshold:
                kwargs['status'] = -402
                kwargs['count'] = kwargs.get('count', 1) + 1
                kwargs['keyword'] = keyword
                err_list.append(kwargs)
            return None
        if data_dict['list']:
            try:
                _fetch_function = getattr(obj, 'fetch_search_list')
            except Exception as e:
                _fetch_function = None
                print(util.traceback_info(e, return_all=1))
            if _fetch_function:
                res = self._crawl(_fetch_function, data_dict['list'], headers, proxy)
                if 'url' in res:
                    for url in res['url']:
                        data_dict['url'].append(url)
                if 'detail' in res:
                    for data in res['detail']:
                        data_dict['detail'].append(data)
        if data_dict['url']:
            try:
                _fetch_function = getattr(obj, 'fetch_data')
            except Exception as e:
                _fetch_function = None
                print(util.traceback_info(e, return_all=1))
            if _fetch_function:
                res = self._crawl(_fetch_function, data_dict['url'], headers, proxy)
                if 'detail' in res:
                    for data in res['detail']:
                        data_dict['detail'].append(data)
        for data in data_dict['detail']:
            if data.get('status') != 200:
                print('已丢弃无效数据')
                continue
            if 'product_id' not in data and 'list' in data and data['list']:
                _data = copy.copy(data)
                del _data['list']
                for row in data['list']:
                    row.update(_data)
                    if 'goods_sn' not in row:
                        continue
                    data_list.append(row)
                continue
            else:
                data_list.append(data)
        return data_list

    def _crawl(self, fn, dlist, headers=None, proxy=None):
        tlist = []
        data_list = []
        i = 0
        for row in dlist:
            # 最大线程，深度URL最大数量
            if i >= self._max_depth:
                break
            if 'id' not in row:
                continue
            row['headers'] = headers
            if isinstance(proxy, dict):
                row['proxies'] = proxy
            else:
                row['proxy'] = proxy
            t = threading.Thread(target=self._fetch_data, args=(fn, data_list), kwargs=row)
            tlist.append(t)
            t.start()
            i += 1

        for t in tlist:
            t.join()

        data_dict = {
            'detail': [],
            'list': [],
            'url': []
        }
        for data in data_list:
            if fn.func_name == 'fetch_data':
                data_dict['detail'].append(data)
            elif fn.func_name == 'fetch_search_list':
                data_dict['detail'].extend(data['detail'])
                data_dict['url'].extend(data['url'])
        return data_dict

    def _fetch_data(self, fn, data_list=[], **kwargs):
        """获取数据"""
        try:
            data = fn(**kwargs)
            # 当function_name为fetch_data时失败或异常返回为状态值
            if isinstance(data, dict):
                data['id'] = kwargs['id']
                data['status'] = 200
                data_list.append(data)
            elif fn.func_name == 'fetch_data':
                del kwargs['headers']
                kwargs['status'] = data
                kwargs['count'] = kwargs.get('count', 1)
                if data in (404, 405):
                    kwargs['list'] = []
                data_list.append(kwargs)
            return data
        except Exception as e:
            print(util.binary_type(e))
            return None

    def get_prolist(self):
        """获取代理列表"""
        prolist = []
        limit = 10 if self.limit < 10 else self.limit
        url = 'http://proxy.elecfans.net/proxys.php?key=nTAZhs5QxjCNwiZ6&num={0}'.format(limit)
        if self.optype == 'hot':
            if self.pay:
                url += '&type=pay'
            else:
                url = url
        try:
            resp = requests.get(url)
            data = json.loads(resp.content)
            for vo in data['data']:
                prolist.append(vo['ip'])
        except:
            config.LOG.exception('get proxy list error')
        _num = len(prolist)
        if _num <= 1:
            return None
        return [_num, prolist]


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-i', '--interval-time', dest='interval', help='间隔时间，默认为1秒，\
                         0则仅运行一次', default=1, type=int)
    act_group = parser.add_argument_group(title='操作选择项')
    act_group.add_argument('-n', '--no-proxy', help='不使用代理，选择将不使用代理更新',
                           action='store_true', default=False)
    act_group.add_argument('-t', '--pay', help='是否使用复位代理,默认不使用',
                           action='store_true', default=False)
    act_group.add_argument('-E', '--exception-threshold', help='异常阈值，超过此数量将记录进mongodb中，默认为5',
                           default=5, type=int)
    act_group.add_argument('-u', '--use', help='更新是否使用接口,默认不使用',
                           action='store_true', default=True)
    act_group.add_argument('-l', '--limit', help='单次更新限制数量，默认为 %s' % config.QUEUE_LIMIT,
                           default=config.QUEUE_LIMIT, type=int)
    act_group.add_argument('-o', '--optype', help='指定队列进行更新，不选默认为所有预更新队列', dest='optype',
                           action='store_const', const='cp', default=2)

    search_group = parser.add_argument_group(title='更新选择项')
    search_group.add_argument('-M', '--max-depth', help='指定搜索最大深度，默认为 10', default=10, type=int)

    notice_group = parser.add_argument_group(title='提醒选择项')
    notice_group.add_argument('--notice', dest='notice', help='更新异常提醒进程(守护进程)，\
        用于监控更新异常情况，默认为False，选择则为True', default=False)
    notice_group.add_argument('--notice-threshold', help='通知阈值(一个小时内)，\
        对于异常记录条数超过阀值的将进行邮件提醒，默认为30', default=30, type=int)
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        print("\n示例")
        print(' 指定更新队列数据                %s -o 2' % sys.argv[0])
        print(' 更新启动异常提醒监控            %s -o 2 --notice' % sys.argv[0])
        print(' 不使用代理获取数据              %s -on 2' % sys.argv[0])
        print()

    if args.optype:
        # optype为1时,获取全部队列进行更新
        if args.optype == 1:
            args.queues = [config.QNAME_KEY[key] for key in config.QNAME_KEY]
        else:
            args.queues = [config.QNAME_KEY[args.optype]]

        while 1:
            UpdateChip(**args.__dict__)
            if args.interval <= 0:
                break
            print('-------------- sleep %s sec -------------' % args.interval)
            time.sleep(args.interval)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
