# -*- coding: utf-8 -*-
# @Time    : 2019/3/19 15:54
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : cp_hot.py
# @Software: PyCharm
# @Remarks : 彩票热度算法尝试~

from packages import yzwl

db = yzwl.DbSession()
mysql = db.yzwl


def get_fc3d_data():
    data = mysql.select('game_sd_result', ('cp_id', 'expect'))
    number_count = {
        'hundreds': {
            '0': 0,
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
            '8': 0,
            '9': 0,
        },
        'tens': {
            '0': 0,
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
            '8': 0,
            '9': 0,
        },
        'units': {
            '0': 0,
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
            '8': 0,
            '9': 0,
        },
    }
    for d in data[:30]:
        code = list(d['cp_id'])
        number_count['hundreds'][code[0]] += 1
        number_count['tens'][code[1]] += 1
        number_count['units'][code[2]] += 1
    print(number_count)


if __name__ == '__main__':
    get_fc3d_data()
