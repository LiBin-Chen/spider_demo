# -*- coding: utf-8 -*-
# @Time    : 2019/3/21 14:31
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : main.py
# @Software: PyCharm
# @Remarks : 控制中心，各大爬虫入口
import argparse

import siteall


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-s', '--src', help=u'来源网站',
                        dest='source', action='store', default=0)
    parser.add_argument('-p', '--past', help=u'下载历史数据',
                        dest='past', action='store', default=0)
    # parser.add_argument('-s', '--sign', help=u'定时任务时使用获取到开奖结果即关闭程序的标记',
    #                     dest='sign', action='store', default=1)
    parser.add_argument('-sd', '--sd', help=u'指定开始下载日期',
                        dest='sd', action='store', default='2010-10-23')
    parser.add_argument('-ed', '--ed', help=u'指定结束下载日期',
                        dest='ed', action='store', default='2019-03-17')
    parser.add_argument('-C', '--cp', help='指定更新彩种(可多选)，不选默认为所有彩种',
                        nargs='+')
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    if not args.cp:
        args.cp = ['4', '5', '6', '8', '9']
    if args.help:
        parser.print_help()
        print(u"\n示例")
