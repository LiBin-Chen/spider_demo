#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''
import random

from packages import yzwl

db = yzwl.DbClass()

mysql = db.local_yzwl


class SD():
    def __init__(self, ball=None):
        self.ball = ball
        pass

    def one(self, length):
        '''
        随机按位杀号
        :return:
        '''
        # 杀1 2 3 4 5
        number_list = []
        while 1:
            if len(number_list) == 10:
                break
            # for i in range(10):
            num = random.randint(0, 9)
            if num not in number_list:
                number_list.append(num)
        print('number_list', number_list)

        return number_list[:length]

    def ten(self):
        '''
        杀十位
        :return:
        '''
        pass

    def hundred(self):
        '''
        杀百位
        :return:
        '''
        pass


# 3d杀码最多杀5码
sd = SD()
expect = 0
total_num = 0
valid_num = 0
while 1:
    data = mysql.select('game_sd_result', condition={'expect':('>',expect)}, fields=('id', 'expect', 'open_code'), limit=1,
                        order='open_time ASC')
    if not data:
        break

    expect = data.get('expect')
    open_code = data.get('open_code')
    code_list = [int(x) for x in open_code.split(',')]

    kill_code = sd.one(4)

    if code_list[0] not in kill_code:
        print('杀对')
        valid_num += 1
    total_num += 1

print('total_num', total_num)
print('valid_num', valid_num)

print('正确率为: ', valid_num / total_num)

