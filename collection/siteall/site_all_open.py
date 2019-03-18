#! /usr/bin/python
# -*- coding: utf-8 -*-
from packages import db

__author__ = 'snow'
__time__ = '2019/3/12'

't_open_info_spider'

mysql = db.local_yzwl

open_data = {
    'jsh_open_url': '',
    'sll_open_url': '',
    'aicai_open_url': '',
    'cwl_open_url': '',
    'five_open_url': '',
}
#
# data = mysql.select('t_lottery_sll',
#                     fields=('id', 'abbreviation', 'lottery_name', 'province', 'lottery_result', 'lottery_chart_url'))
#
# for _data in data:
#     abbreviation = _data['abbreviation']
#     print('abbreviation:{0}  lottery_name:{1}   province:{2}  lottery_chart_url:  {3}'.format(abbreviation,
#                                                                                               _data['lottery_name'],
#                                                                                               _data['province'],
#                                                                                               _data[
#                                                                                                   'lottery_chart_url']))
    # print("'{0}':'',".format(abbreviation))
#
# exit()
'''
地区，彩种，key_name，数据库
'''

# for key in data_dict:
#     info = mysql.select('t_open_info_spider', condition={'abbreviation': key}, limit=1)
#     if not info:
#         print('不存在： ', key)
#     else:
#         mysql.update('t_open_info_spider', condition={'abbreviation': key}, data={'jsh_open_url': data_dict[key]})
#         print('更新数据成功..')

KEY_DICT = {
    'lotto': '',
    'pk10': 'https://www.pk10.me/draw-pk10-today.html',
    'pl3': '',
    'jczq': '',
    'jclq': '',
    'gd11x5': '',
    'ssq': '',
    'aheswxw': '',
    'zjesxw': '',
    'sd': '',
    'qlc': '',
    'plw': '',
    'qxc': '',
    'fjsslxq': '',
    'gdfcsslxq': '',
    'gxklsc': '',
    'hnsjy': '',
    'hebfcesxw': '',
    'hnfcesxw': '',
    'hljeexw': '',
    'hbfcesxw': '',
    'hdswxw': '',
    'jsqws': '',
    'lnsswxq': '',
    'shttcx4': '',
    'czfc': '',
    'xjfceswxq': '',
    'gssyxw': '',
    'bjkzc': '',
    'gdklsf': 'https://www.pk10.me/draw-gdkl10-today.html',
    'gxklsf': '',
    'hnbxs': '',
    'hebsyxw': '',
    'hljklsfmj': '',
    'hbsyxw': '',
    'jxsyxw': '',
    'lnklse': '',
    'nmgssc': '',
    'qhsyxw': '',
    'sfc': '',
    'rx9': '',
    'nmgsyxw': '',
    'lnsyxw': '',
    'jlsyxw': '',
    'xjsyxw': '',
    'ynsyxw': '',
    'shxsyxw': '',
    'sxsyxw': '',
    'gzsyxw': '',
    'shxklsf': '',
    'sxklsf': '',
    'chqklsf': '',
    'hnklsf': '',
    'hljklsf': '',
    'tjklsf': '',
    'xjssc': 'https://www.pk10.me/draw-xjssc-today.html',
    'ynssc': '',
    'cqssc': 'https://www.pk10.me/draw-cqssc-today.html',
    'tjssc': 'https://www.pk10.me/draw-tjssc-today.html',
    'qhk3': '',
    'gsk3': '',
    'gzk3': '',
    'gxk3': '',
    'hbk3': '',
    'henk3': '',
    'jxk3': '',
    'fjk3': '',
    'ahk3': '',
    'jsk3': 'https://www.pk10.me/draw-jsk3-today.html',
    'shk3': '',
    'jlk3': '',
    'nmgk3': '',
    'hebk3': '',
    'bjk3': '',
    'hljsyxw': '',
    'shsyxw': '',
    'jssyxw': '',
    'zjsyxw': '',
    'ahsyxw': '',
    'fjsyxw': '',
    'bjkl8': '',
    'zjkl12': '',
    'sckl12': '',
    'lnkl12': '',
    'shssl': '',
    'xjxlc': '',
    'hnxysc': '',
    'henky481': '',
    'sdklpk3': '',
    'sdqyh': '',
    'gxsyxw': '',
}

for key in KEY_DICT:
    mysql.update('t_open_info_spider', condition={'abbreviation': key}, data={'pks_open_url': KEY_DICT[key]})
    print('更新成功')
