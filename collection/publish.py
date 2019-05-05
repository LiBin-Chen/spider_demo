#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
import sys
import time
import config
import logging
import argparse
from packages import yzwl
from packages import rabbitmq
from packages import Util as util

try:
    import json
except ImportError:
    import simplejson as json

# global object
db = yzwl.DbClass()
mysql = db.yzwl
mq = rabbitmq.RabbitMQ()
collection = db.mongo['collection_name']
_logger = logging.getLogger('demo_spider')

'''持久化存储模块

@description
    数据出口
'''


class PublishChip(object):
    """提交队列数据入库"""

    def __init__(self, **kwargs):
        self._init_args(**kwargs)
        self.run()

    def run(self):
        """运行"""
        handler = getattr(self, 'get_update_data')  # 更新数据
        handler()

    def _init_args(self, **kwargs):
        """初始化参数"""
        self.no_proxy = kwargs.get('no_proxy')
        self.exception_threshold = kwargs.get('exception_threshold', 5)
        self.notice_threshold = kwargs.get('notice_threshold', 30)
        self.limit = kwargs.get('limit', 10)

        self._max_depth = kwargs.get('max_depth', 10)

    def check_exists(self, data, condition=None):
        """
        检测是否存在,已存在返回True，否则返回False
        可加入其它去重方式
        """
        if not condition:
            return {}
        try:
            # ret = collection.find_one(condition)  # mongodb去重
            info = mysql.select(data['demo'], condition=condition, limit=1)  # mysql去重
            if info:
                print('该数据已存在: {0}'.format(data['demo']))
                return info
            else:
                # if not ret:
                #     collection.save(data)
                return {}
        except Exception as e:
            print('mongodb 操作异常，异常原因: %s' % (util.binary_type(e),))
            return {}

    def get_update_data(self):
        queue_name = config.WAIT_UPDATE_QUEUE
        qsize = mq.qsize(queue_name)
        limit = self.limit if qsize > self.limit else qsize  # 每次更新的数量
        queue_list = []
        for i in range(limit):
            queue_data = mq.get(queue_name)
            if queue_data not in queue_list:  # 重复的数据不需要
                queue_list.append(queue_data)

        if not queue_list:
            print('等待中，队列 %s 为空' % queue_name)
            return 0
        valid_num = 0
        total_num = 0
        # 本次入库的总数
        total_num = len(queue_list)
        for data in queue_list:
            # 无效队列数据
            '''
            #进行入库前的二次清洗
            #可定义入库规则.去重规则和索引规则
            #可同时推送至队列或者elasticsearch等第三方
            '''
            expect = 'demo'
            data['expect'] = expect
            condition = {'expect': expect}
            info = self.check_exists(data, condition)
            if info:
                valid_num += 1
            self.save_data(data, info)

    def save_data(self, data, info):
        db_name = data.get('demo', '')
        try:
            if not info:
                mysql.insert(db_name, data=data)
                _logger.info('INFO:  DB:%s 数据保存成功, 期号 %s ; 产品:%s' % (db_name, data['expect'], data.get('name')))
            else:
                data['create_time'] = info['create_time']
                data['update_time'] = util.date()
                mysql.update(db_name, condition={"id": info["id"]}, data=data)
                _logger.info('INFO:  DB:%s 数据更新成功, 期号 %s ; 产品: %s' % (db_name, data['expect'], data.get('name')))

        except Exception as e:
            _logger.info('INFO:  DB:%s 数据保存失败 %s, 期号 %s ; 产品: %s ' % (db_name, e, data['expect'], data.get('name')))


def main():
    # 将预提交数据存入数据库中
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-i', '--interval-time', dest='interval', help='间隔时间，默认为2秒，\
                         0则仅运行一次', default=2, type=int)
    act_group = parser.add_argument_group(title='操作选择项')
    act_group.add_argument('-o', '--optype', help='指定队列进行更新，不选默认为所有预更新队列', dest='optype',
                           action='store_const', const='cp', default=1)
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        print("\n示例")
        print(' 指定更新队列数据                %s -o 2' % sys.argv[0])
        print()

    if args.optype:
        # optype为1时,获取全部队列进行更新
        if args.optype == 1:
            args.queues = [config.QNAME_KEY[key] for key in config.QNAME_KEY]
        else:
            args.queues = [config.QNAME_KEY[args.optype]]
        while 1:
            PublishChip(**args.__dict__)
            if args.interval <= 0:
                break
            print('-------------- sleep %s sec -------------' % args.interval)
            time.sleep(args.interval)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
