#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''

import json
import time
import pandas as pd
from packages import yzwl

db = yzwl.DbClass()

mysql = db.local_yzwl

'''
3D:   独胆  杀一码  杀二码  杀三码


球号
玩法  杀几码
结果验证



福彩3d技巧大汇总3D杀号公式   
1．   和值乘百位＋1除3的余数再－3，杀以余数为尾的和值  （80％）   
2．   和值乘百位＋1除3的余数，杀余数路的和值 （80％）   
3．   相邻开奖号的各位数的差的和杀和值及和尾 （89％）   
4．   上期跨杀和值及和尾 （93％）   

5．   相邻开奖号的差的各位和杀和值及和尾 （86％）   
6．   两相邻同和尾的上期奖号的下期奖号和值杀和尾 （92％）   
7．   上期和值杀本期跨度（88％） 
  
8．   和值尾＋4,绝杀个位 （91％）   
9．   上期跨度，绝杀个位 （92％）
'''


class KillNumber():
    def __init__(self, ball, play_type, check_number=None):
        self.ball = ball
        self.play_type = play_type
        self.check_number = check_number

    def run(self):
        pass

    def random_two(self):
        '''
        杀个位
        :return:
        '''
        print(self.ball)
        code_list = [int(x) for x in self.ball.split(',')]
        _sum = sum(code_list)
        print('_sum', _sum)
        pass


# data = {'id': 2154, 'open_code': '6,7,0', 'expect': '2013002'}
# k = KillNumber(ball='6,7,0', play_type='h1')
# k.random_two()
#
# exit()


def main():
    expect = '0'
    # big_list = {}
    while 1:
        data = mysql.select('game_sd_result', condition={'expect': ('>', expect)},
                            fields=('id', 'open_code', 'expect'),
                            order='expect ASC',
                            limit=1)
        print('data', data)

        expect = data.get('expect')


def kill(expect):
    data = mysql.select('game_sd_result', condition={'expect': ('>', expect)},
                        fields=('id', 'open_code', 'expect'),
                        order='expect ASC',
                        limit=1)
    # print('data', data)
    if not data:
        return 404

    expect = data.get('expect')
    open_code = data.get('open_code')
    code_list = [int(x) for x in open_code.split(',')]
    number1 = code_list[1]
    # 上期十位杀本期个位 （90％）
    return check(expect, number1)


def check(expect, number1):
    data = mysql.select('game_sd_result', condition={'expect': ('>', expect)},
                        fields=('id', 'open_code', 'expect'),
                        order='expect ASC',
                        limit=1)
    # expect = data.get('expect')
    open_code = data.get('open_code')
    code_list = [int(x) for x in open_code.split(',')]
    print(code_list[0] )
    print(number1 )
    if code_list[0] == number1:
        print('杀对')
        return True
    print('杀错')
    return False


if __name__ == '__main__':
    # main()
    total = 0
    valid = 0
    while 1:
        result = kill(0)
        total += 1
        if result and result != 404:
            valid += 1

        elif result == 404:
            break

        else:
            pass

    print('total', total)
    print('valid', valid)

    print('杀号正确率: ', valid / total)
