#! /usr/bin/python
# -*- coding: utf-8 -*-
import random
import time
from itertools import product

__author__ = 'snow'
__time__ = '2019/3/29'

'''
http://www.shenshengjihua.com:8080/shensheng/getdata?cz=1&qi=0&jhid=825&jhflag=&uid=2343950&t=a63feb658eab8076&sign=860f6b6842c0f7ac4af9b812c7985ffe

'''
from packages import Util as util, yzwl, rabbitmq

db = yzwl.DbClass()
mysql = db.yzwl
numberList = list(range(0, 12))

print('numberList', numberList)
expect = 731413
# while 1:
#     choiceList = random.sample(numberList, 5)
#
#     print('choiceList', choiceList)
#
#     data = mysql.select('game_pk10_result', fields=('expect', 'open_code', 'open_time'), condition={'expect': expect},
#                         limit=1)
#     # if not data:
#     #     interval = ts + 1200
#     #     if int(time.time())<interval
#     #     print('---------- sleep {0}s ----------'.format(interval))
#     #     time.sleep(interval)  # 暂停间隔时间
#     #     continue
#     if not data:
#         break
#     # expect = data['expect']
#     open_code = data['open_code']
#     open_time = data['open_time']
#     timeArray = time.strptime(str(open_time), "%Y-%m-%d %H:%M:%S")
#     ts = int(time.mktime(timeArray))
#     print('expect', expect)
#     # print('open_code', open_code)
#     # print('open_time', open_time)
#
#     # 中奖
#     print(open_code[0])
#     if int(open_code[0]) in choiceList:
#         print('中奖')
#
#     expect = int(expect)
#     expect += 1

proNameList = ['作茧自缚', '古月道人 ', '庖丁解牛 ', '海阔天空', ' 天长地久', ' 岁寒三友', ' 南柯一梦', ' 群雄逐鹿', ' 天罗地网', ' 衣冠禽兽', ' 笼中之鸟', '惊弓之鸟',
               '计划大师', '天师归来', '七情六欲', '蓝仙子', '龙生九子', '无忧无虑', '悬崖勒马', '二五八万']

mq = rabbitmq.RabbitMQ()

qname = 'lottery_open_result'

while 1:
    if not mq.qsize(qname):
        continue
    lotteryData = mq.get_queue_list(qname)
    print('lotteryData', lotteryData)
