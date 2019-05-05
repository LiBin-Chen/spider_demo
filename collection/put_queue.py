#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import time
import logging
import argparse

try:
    import json
except ImportError:
    import simplejson as json

import config
from packages import yzwl
from packages.daemon import Daemon
from packages import rabbitmq
from packages import Util as util


'''爬虫入口模块

@description
    提交需要更新的产品至队列,可制定采集规则
'''


queue = rabbitmq.RabbitMQ()
db = yzwl.DbClass()
mysql = db.yzwl
_logger = logging.getLogger('demo_spider')


class PutQueue:

    def __init__(self, **kwargs):
        self._init_args(**kwargs)
        self._check_qsize()
        self.get_put_message()

        print('Done!')
        _logger.info('INFO: {0} 成功提交更新产品 {1} 数量: {2}'.format(self.qname, self.lottery_type, self._total_number))

    def _init_args(self, **kwargs):
        """初始化参数"""
        self._total_number = 0
        self.__mongo = None
        self.qname = None
        self.__del = set()
        self.supplier = kwargs.get('supplier')  # 指定id进行更新
        self.lotto_type = kwargs.get('lotto_type', '')  # 指定更新产品类型
        # self.start_id = kwargs.get('start_id', 0)  # 指定起始id进行更新
        # self.end_id = kwargs.get('end_id', 0)  # 指定结束id进行结束
        self.threshold = kwargs.get('threshold', 0)
        self.all = kwargs.get('all', False)
        self.multi_url = kwargs.get('multi_url', True)
        self.expire_time = kwargs.get('expire_time', config.DATA_CACHE_TIME)  # 过期时间

    def _check_qsize(self):
        if self.threshold > 0:
            while 1:
                qsize = queue.qsize(queue_name=self.qname)
                if qsize < self.threshold:
                    break
                print('当前队列数目为 %s 超过设置的最大值 %s ，等待中...' % (qsize, self.threshold))
                time.sleep(10)

    def get_put_message(self):
        '''
        获取需要更新的产品数据并且提交到队列
        :return:
        '''
        '''
        #在此进行更新数据源的调度
        #调度规则可根据实际进行选择
        #可将产品提供到不同的队列
        eg: 
        1.产品距离上次更新的时间
        2.是否是需要类型的产品
        3.更新产品的 请求url是什么
        4......
        
        '''

        return self._total_number


def run(args):
    if not isinstance(args, argparse.Namespace):
        print('参数有误')
        return
    interval = args.interval
    while 1:
        try:
            PutQueue(**args.__dict__)
            if args.interval <= 0:
                break
            print('------------- sleep %s sec -------------' % interval)
            time.sleep(interval)
        except Exception as e:
            if 'params_error' in e:
                break
            print(util.traceback_info(e, return_all=True))


# class PutQueueServer(Daemon):
#     '''
#     守护进程运行模式
#     '''
#
#     def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', **kwargs):
#         self.args = kwargs.get('args', args)
#         super(SearchChipServer, self).__init__(pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
#
#     def run(self):
#         run(self.args)


def main():
    parser = argparse.ArgumentParser(description="提交更新产品至更新队列", add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-a', '--all', dest='all', help='提交全部产品至更新队列,默认为否', action='store_true')
    parser.add_argument('-L', '--lotto-type', dest='lotto_type', help='从数据库提交指定产品到对应产品队列', type=int,
                        default=0)  # 2,3,4,5,6
    parser.add_argument('-s', '--supplier', dest='supplier', help='指定产品ID进行更新', type=int, default=0)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认5s)，小于或等于0时则只会执行一次',
                        default=0, type=int)
    parser.add_argument('-p', '--supplier-list', help='打印产品表/产品类型',
                        action='store_true', default=False)
    # parser.add_argument('-S', '--start-id', dest='start_id', help='指定提交的起始',
    #                     default=0, type=int)
    # parser.add_argument('-E', '--end-id', dest='end_id', help='指定提交的起始',
    #                     default=0, type=int)
    parser.add_argument('-q', '--queue-max-num', dest='threshold',
                        help='指定队列数量最大提交阀值，即更新队列数量小于该数目时提交更新队列\
                        （默认10，小于或等于0时为不限制）', default=0, type=int)

    parser.add_argument('-e', '--expire-time', help='指定数据有效期(单位秒)，默认为 %s' %
                                                    config.DATA_CACHE_TIME, default=config.DATA_CACHE_TIME, type=int)
    args = parser.parse_args()
    mysql = db.yzwl
    data = mysql.select('demo_mysql', fields=('id', 'product_name'))
    supplier_list = [_data['id'] for _data in data]
    if args.supplier:
        if args.supplier not in supplier_list:
            print('请至少选择一个有效的产品ID')
            sys.exit(-1)
    if args.help:
        parser.print_help()
        print("\n示例")
        print(' 指定需要提交的产品       %s -s 20' % sys.argv[0])
        print(' 指定起始ID（仅第一次）   %s -s 20 --start-id 1' % sys.argv[0])
        print(' 设置队列最大提交阀值     %s -s 20 -q 1000000' % sys.argv[0])
        print(' 设置过期时间如2天        %s -s 20 -e 172800' % sys.argv[0])
    elif args.supplier_list:
        type_dict = dict(zip(config.QNAME_KEY.keys(), config.QNAME_DICT.keys()))
        print('产品类型:')
        print('产品类型:', type_dict)
        print('\n')
        print('产品列表:')
        print('产品列表:', data)
    elif args.lotto_type or args.all or args.supplier:
        type_list = [2, 3, 4, 5, 6]
        if args.lotto_type and args.lotto_type not in type_list:
            print('请选择一个有效的产品类型 : {0}'.format(type_list))
            sys.exit()
        run(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
