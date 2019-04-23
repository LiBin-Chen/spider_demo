#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import logging
import re
import sys
import time
import select
import socket
import argparse

try:
    import json
except ImportError:
    import simplejson as json

import pika
import requests
import pymongo

import config
from packages import Util as util
from packages import yzwl
from packages.daemon import Daemon
from packages import rabbitmq

'''
提交需要更新的产品至队列
'''

queue = rabbitmq.RabbitMQ()
db = yzwl.DbClass()
mysql = db.local_yzwl
_logger = logging.getLogger('yzwl_spider')


class PutQueue:

    def __init__(self, **kwargs):
        self._init_args(**kwargs)
        self._check_qsize()
        self.get_put_message()

        print('Done!')
        _logger.info('INFO: 成功提交更新彩种数量: {1}'.format(self.qname, self._total_number))
        # _logger.info('INFO: 提交队列: {0} ; 提交更新彩种数量: {1}'.format(self.qname, self._total_number))

    def _init_args(self, **kwargs):
        """初始化参数"""
        self._total_number = 0
        self.__mongo = None
        self.qname = None
        self.__del = set()
        self.supplier = kwargs.get('supplier')  # 指定id进行更新
        self.lotto_type = kwargs.get('lotto_type', '')  # 指定更新彩种类型
        self.start_id = kwargs.get('start_id', 0)  # 指定起始id进行更新
        self.threshold = kwargs.get('threshold', 0)
        self.all = kwargs.get('all', False)
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
        获取需要更新的彩种数据并且提交到队列
        :return:
        '''
        # 过期时间
        condition = {}
        if self.lotto_type in config.QNAME_KEY.keys():
            type_dict = dict(zip(config.QNAME_DICT.values(), config.QNAME_DICT.keys()))  # 获取指定的彩种类型
            lottery_type = type_dict[config.QNAME_KEY[self.lotto_type]]
            condition = {'id': ('>=', self.start_id), 'lottery_type': lottery_type}

        fields = ('id', 'abbreviation', 'lottery_name', 'lottery_type', 'update_url', 'lottery_result', 'province')

        '''
        更新模式:
        1.指定彩种类型更新 id=0 lottery_type=彩种类型
        2.指定彩种id   id=1   
        3.所有彩种进行更新,无指定彩种类型则全部更新  id=0 
        
        '''

        if self.all:
            # 提交全部彩种至队列
            data = mysql.select('t_lottery', fields=fields)
        elif self.supplier:
            # 对指定的彩种进行更新
            data = mysql.select('t_lottery', condition=[('id', '=', self.supplier)], fields=fields)
        elif condition:
            # 根据起始id和彩种类型进行更新  eg: id>0 类型为高频  #常用方法为指定彩种类型进行更新
            data = mysql.select('t_lottery', condition=condition, fields=fields)
        else:
            print('参数有误..')

        self._total_number = len(data)

        for vo in data:
            vo['lottery_name'] = vo['province'] + vo['lottery_name']
            del vo['province']

            self.qname = config.QNAME_DICT.get(vo['lottery_type'], '')  # 根据彩种类型推送至不同的队列
            if not self.qname or not vo.get('update_url'):
                message = '队列qname为空' if not self.qname else '更新url为空'
                _logger.info('ID: {0} ;提交更新失败: {1}  ; {2}'.format(vo['id'], vo['lottery_name'], message))
                self._total_number -= 1
                continue
            queue.put(self.qname, vo)
        return self._total_number


def run(args):
    if not isinstance(args, argparse.Namespace):
        print('参数有误')
        return
    sleep_time = args.sleep_time
    while 1:
        try:
            PutQueue(**args.__dict__)
            if args.sleep_time <= 0:
                break
            print('------------- sleep %s sec -------------' % sleep_time)
            time.sleep(sleep_time)
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
    parser = argparse.ArgumentParser(description="提交更新彩种至更新队列", add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-a', '--all', dest='all', help='提交全部彩种至更新队列,默认为否', action='store_true', default=False)
    parser.add_argument('-lt', '--lotto-type', dest='lotto_type', help='从数据库提交指定彩种到对应产品队列', type=int,
                        default=2)  # 2,3,4,5,6
    parser.add_argument('-s', '--supplier', dest='supplier', help='指定彩种ID进行更新', type=int)
    parser.add_argument('-t', '--sleep-time', dest='sleep_time',
                        help='指定暂停时间(默认5s)，小于或等于0时则只会执行一次',
                        default=120, type=int)
    parser.add_argument('-p', '--supplier-list', help='打印彩种列表/彩种类型',
                        action='store_true', default=False)
    parser.add_argument('--start-id', dest='start_id', help='指定提交的起始',
                        default=0, type=int)
    parser.add_argument('-q', '--queue-max-num', dest='threshold',
                        help='指定队列数量最大提交阀值，即更新队列数量小于该数目时提交更新队列\
                        （默认10，小于或等于0时为不限制）', default=0, type=int)

    parser.add_argument('-e', '--expire-time', help='指定数据有效期(单位秒)，默认为 %s' %
                                                    config.DATA_CACHE_TIME, default=config.DATA_CACHE_TIME, type=int)
    args = parser.parse_args()
    mysql = db.local_yzwl
    data = mysql.select('t_lottery', fields=('id', 'lottery_name'))
    supplier_list = [_data['id'] for _data in data]
    if args.supplier:
        if args.supplier not in supplier_list:
            print('请至少选择一个有效的彩种ID')
            sys.exit(-1)
    if args.help:
        parser.print_help()
        print("\n示例")
        print(' 指定需要提交的彩种       %s -s 20' % sys.argv[0])
        print(' 指定起始ID（仅第一次）   %s -s 20 --start-id 1' % sys.argv[0])
        print(' 设置队列最大提交阀值     %s -s 20 -q 1000000' % sys.argv[0])
        print(' 设置过期时间如2天        %s -s 20 -e 172800' % sys.argv[0])
    elif args.supplier_list:
        type_dict = dict(zip(config.QNAME_KEY.keys(), config.QNAME_DICT.keys()))
        print('彩种类型:')
        print('彩种类型:', type_dict)
        print('彩种列表:')
        print('彩种列表:', data)
    else:
        print('args', args)
        run(args)


if __name__ == '__main__':
    main()
