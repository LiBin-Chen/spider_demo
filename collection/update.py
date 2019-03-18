# -*- coding: utf-8 -*-


__author__ = 'snow'
__time__ = '2019/3/3'

# bulit-in
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
import config
import requests
from packages import rabbitmq, supplier
from packages import yzwl
from packages import Util as util

db = yzwl.DbClass()
mq = rabbitmq.RabbitMQ()

mysql = db.local_yzwl


class UpdateData(object):
    """更新数据"""

    def __init__(self, **kwargs):
        self._init_args(**kwargs)
        self.run()

    def _init_args(self, **kwargs):
        """初始化参数"""
        # print('kwargs', kwargs)
        self.action = kwargs.get('action', 'put')
        self.no_proxy = kwargs.get('no_proxy')  # 是否使用代理
        # if self.action == 'search' and not kwargs.get('optype'):
        #     self.dblist = [config.SEARCH_UPDATE_QUEUE]
        # else:
        self.flist = kwargs.get('flist', [])
        self.exception_threshold = kwargs.get('exception_threshold', 5)
        self.notice_threshold = kwargs.get('notice_threshold', 30)
        self.notice = kwargs.get('notice')
        self.limit = kwargs.get('limit', config.QUEUE_LIMIT)
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
        qnum = len(self.flist)
        handler = getattr(self,
                          'search_data' if self.action == 'search' and self.optype == 'hot' else 'update_data')  # 选择何种操作

        if qnum > 1:
            plist = []
            for db_field in self.flist:
                wid = self.suppliers[self.flist.index(db_field)]
                p = multiprocessing.Process(target=handler, args=(wid, db_field,))  # 每个网站(字段)开一个独立进程
                plist.append(p)
                p.start()
            for p in plist:
                p.join()
        else:
            wid = self.suppliers[0]
            handler(wid, self.flist[0])

    def get_prolist(self, limit):
        count = mysql.count('proxies') - limit
        end_number = random.randint(1, count)
        condition = [('pid', '>=', end_number), ('is_pay', '=', 1), ('is_use', '=', 1)]
        data = mysql.select('proxies', condition=condition, limit=limit)
        if isinstance(data, dict):
            return {'ip': data['ip']}
        dlist = []
        for _data in data:
            item = {
                'ip': _data['ip'],
            }
            dlist.append(item)
        return dlist
    def update_data(self, wid, db_field=None):
        """更新指定队列数据"""
        if not db_field or not wid:
            return 0
        # print('wid', wid)
        # if not db_field:
        #     print('等待中，队列 %s 为空' % db_field)
        #     return 0
        # print('wid', wid)
        proxy = None
        if not self.no_proxy:
            proxy = self.get_prolist()
        tlist = []
        data_list = []
        total_num = 0
        data = None
        fields = (db_field, 'lottery_result', 'lottery_type')

        url_data = mysql.select('t_lottery', fields=fields)
        for _data in url_data:
            # _url 为空

            url = _data.get(db_field)
            db_name = _data.get('lottery_result')
            if not url:
                continue

            total_num += 1
            kwargs = {
                'wid': wid,
                'lottery_type': _data.get('lottery_type', ''),
                'db_name': _data.get('lottery_result', '')
            }
            self.fetch_update_data(url, data_list, proxy, **kwargs)
        #     t = threading.Thread(target=self.fetch_update_data,
        #                          args=(url, data_list, proxy), kwargs=kwargs)
        #     tlist.append(t)
        #     t.start()
        #     time.sleep(0.1)
        #
        # try:
        #     for t in tlist:
        #         t.join(45)
        # except (KeyboardInterrupt, SystemExit):
        #     print('pass')
        #     mq.put_queue_list(queue_name, queue_list)
        #     return 0
        # del queue, queue_list

        # valid_num = 0
        # valid_dict = {}
        # delete_list = []
        # update_list = []
        # for data in data_list:
        #     key = int(str(data['id'])[0:2])
        #     if data['status'] > 0:
        #         cnt = 1
        #         if key in valid_dict:
        #             if 'list' in data:
        #                 cnt = len(data['list'])
        #                 valid_dict[key] += cnt
        #             elif 'dlist' in data:
        #                 cnt = sum([(len(row['list']) if 'list' in row else 1) for row in data['dlist']])
        #                 valid_dict[key] += cnt
        #             else:
        #                 valid_dict[key] += 1
        #         else:
        #             valid_dict[key] = 1
        #         valid_num += cnt
        #         if data['status'] == 404 or data['status'] == 405:
        #             delete_list.append(data)
        #             continue
        #
        #         del data['status']
        #         if key == 12 and 'list' in data:
        #             dlist = data['list']
        #         elif 'dlist' in data:
        #             dlist = data['dlist']
        #         else:
        #             dlist = [data]
        #         for row in dlist:
        #             mq.put(config.WAIT_UPDATE_QUEUE, row)
        #
        #     elif data['status'] <= 0:
        #         if data.get('count', 1) < self.exception_threshold:
        #             config.LOG.info('ID：%s，更新状态：%s, 重新入队中!' % (data['id'], data['status']))
        #             update_list.append(data)
        #         else:
        #             config.LOG.error('ID：%s，更新状态：%s, 重试次数超过阀值,保存日志中!' % (data['id'], data['status']))
        #             if 'count' in data:
        #                 del data['count']
        #             data['key'] = key
        #             if 'time' not in data:
        #                 data['time'] = int(time.time())
        #             # db.mongo['update_exception_logs'].insert(data)
        #             mq.put('update_exception_logs', data)
        # # 提交信息
        # mq.put_queue_list(config.DELETE_QUEUE, delete_list)
        # mq.put_queue_list(queue_name, update_list)
        # # 记录更新信息
        # self.write_update_info(valid_dict)
        # print('队列 %s 本次共有 %s 条数据更新成功，成功率：%s %%' %
        #       (queue_name, valid_num, valid_num * 1.0 / total_num * 100 if total_num > 0 else 0))
        # print('完成 , 等待下一个队列!')
        # print('*' * 50)

    def search_data(self, queue_name=None):
        """搜索指定队列数据"""
        if not queue_name:
            return 0
        exchange = 'hqchip_search_queue'
        queue_list = mq.get_queue_list(queue_name=queue_name, limit=self.limit, exchange=exchange)
        if not queue_list:
            print('等待中，队列 %s 为空' % queue_name)
            return 0
        proxy = None
        if not self.no_proxy:
            proxy = self.get_prolist()
        supp_name = queue_name.split('_')[2]
        supp = self._supp_dict[supp_name]
        tlist = []
        data_list = []
        err_list = []
        total_num = 0
        for queue in queue_list:
            # 无效队列数据
            if 'keyword' not in queue:
                continue
            total_num += 1
            t = threading.Thread(target=self.fetch_search_data, args=(data_list, err_list, proxy, supp),
                                 kwargs=queue)
            tlist.append(t)
            t.start()
            time.sleep(0.1)

        try:
            for t in tlist:
                t.join(300)
        except (KeyboardInterrupt, SystemExit):
            mq.put_queue_list(queue_name, queue_list)
            return 0
        del queue, queue_list

        valid_num = len(data_list)
        # 提交信息
        mq.put_queue_list(config.WAIT_ADD_QUEUE, data_list)
        mq.put_queue_list(queue_name, err_list)
        print('队列 %s 本次共有 %s 条数据搜索成功，成功率：%s %%' %
              (queue_name, valid_num, valid_num * 1.0 / total_num * 100 if total_num > 0 else 0))
        print('完成 , 等待下一个队列!')
        print('*' * 50)

    def write_update_info(self, num_list):
        '''记录更新信息

        @param num_list     为更新数目信息
        @param name         记录类型值，默认count为成功值
        '''
        if not num_list:
            return None
        mq.put('crawler_update_stats', {'data': num_list, 'time': util.unixtime()})

    def fetch_update_data(self, url, data_list=[], proxy=None, **kwargs):
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
        # print('id',kwargs.get('id'))
        supplier_name = config.get_web_url(kwargs.get('wid'))  # 获取该程序
        if supplier_name is None:
            return
        headers = {
            'user-agent': random.choice(config.USER_AGENT_LIST),
        }
        try:
            if not hasattr(supplier, supplier_name):
                module_name = 'supplier.{0}'.format(supplier_name)
                if module_name not in sys.modules:
                    __import__(module_name)
                obj = sys.modules[module_name]
            else:
                obj = getattr(supplier, supplier_name)
            _fetch_update_data = getattr(obj, 'fetch_update_data')
        except Exception as e:
            config.LOG.exception('STATUS: -401, URL: {0}'.format(url))
            kwargs['status'] = -401
            data_list.append(kwargs)
            return None
        try:
            kwargs['headers'] = headers
            kwargs['proxy'] = proxy
            data_list.append(_fetch_update_data(url, **kwargs))
        except Exception as e:
            kwargs['status'] = -402
            if 'headers' in kwargs:
                del kwargs['headers']
            if 'proxy' in kwargs:
                del kwargs['proxy']
            data_list.append(kwargs)
            config.LOG.exception('STATUS: -402, URL: {0}'.format(url))
        # print('data_list',data_list)

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
                         0则仅运行一次', default=60, type=int)

    act_group = parser.add_argument_group(title='操作选择项')
    act_group.add_argument('-p', '--put', dest='action', help='更新提交队列数据',
                           action='store_const', const='put', default='put')
    # act_group.add_argument('-s', '--search', dest='action', help='更新搜索时需要更新的产品数据',
    #                        action='store_const', const='search')
    act_group.add_argument('-n', '--no-proxy', help='不使用代理，选择将不使用代理更新',
                           action='store_true', default=False)
    act_group.add_argument('-S', '--supplier', help='指定更新彩种网站数据(可多选)，不选默认为所有网站',
                           nargs='+')
    act_group.add_argument('-E', '--exception-threshold', help='异常阈值，超过此数量将记录进mongodb中，默认为5',
                           default=5, type=int)
    act_group.add_argument('-U', '--use', help='彩种数据更新是否使用接口,默认不使用',
                           action='store_true', default=False)
    act_group.add_argument('--limit', help='单次更新限制数量，默认为 %s' % config.QUEUE_LIMIT,
                           default=config.QUEUE_LIMIT, type=int)

    search_group = parser.add_argument_group(title='更新选择项')
    # search_group.add_argument('-H', '--hot-keyword', help='指定更新彩种产品队列', dest='optype',
    #                           action='store_const', const='hot')
    search_group.add_argument('-M', '--max-depth', help='指定搜索最大深度，默认为 10', default=10, type=int)

    notice_group = parser.add_argument_group(title='提醒选择项')
    notice_group.add_argument('--notice', dest='notice', help='更新异常提醒进程(守护进程)，\
        用于监控更新异常情况，默认为False，选择则为True', default=False)
    notice_group.add_argument('--notice-threshold', help='通知阈值(一个小时内)，\
        对于异常记录条数超过阀值的将进行邮件提醒，默认为30', default=30, type=int)
    args = parser.parse_args()

    if args.help:
        print('args', args)
        parser.print_help()
        print("\n示例")
        print(' 更新提交队列数据                %s -p' % sys.argv[0])
        print(' 指定网站获取更新彩种数据      %s -p --supplier 11 12' % sys.argv[0])
        print(' 更新启动异常提醒监控            %s -p --notice' % sys.argv[0])
        print(' 更新搜索提交数据                %s -s' % sys.argv[0])
        print(' 不使用代理获取数据              %s -pn' % sys.argv[0])
        print()

    elif args.action:
        for k in config.DB_KEY:
            name = 'supplier.' + config.DB_KEY[k]
            try:
                __import__(name)
            except ImportError:
                pass
        # if not args.optype:
        #     args.optype = 'default'
        args.action = 'open'  # open为开奖结果， put为获取某个时间段至今的所有数据
        qtype = 'lottery' if args.action == 'put' else args.action
        args.supplier = [11]  # 11ok

        if not args.supplier:
            slist = []
            for k in config.DB_KEY:
                op_field = '{0}_{1}_{2}'.format(config.URL_KEY[k], qtype, 'url')
                print('op_field', op_field)
                # if mq.existed(qname):
                slist.append(k)
            args.supplier = slist
        flist = []
        for k in args.supplier:
            if int(k) not in config.URL_KEY:
                continue
            op_field = '{0}_{1}_{2}'.format(config.URL_KEY[k], qtype, 'url')
            flist.append(op_field)
        args.flist = flist
        if not args.flist:
            raise ValueError('没有选择有效的字段')
            pass
        while 1:
            UpdateData(**args.__dict__)
            if args.interval <= 0:
                break
            print('-------------- sleep %s sec -------------' % args.interval)
            time.sleep(args.interval)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
