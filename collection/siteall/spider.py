# -*- coding: utf-8 -*-
# @Time    : 2019/3/21 14:31
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : spider.py
# @Software: PyCharm
# @Remarks : 控制中心，各大爬虫入口
import argparse

import siteall


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-sr', '--source', help=u'来源网站',
                        dest='source', action='store', default=0)
    parser.add_argument('-p', '--past', help=u'下载历史数据',
                        dest='past', action='store', default=0)
    parser.add_argument('-s', '--sign', help=u'定时任务时使用获取到开奖结果即关闭程序的标记',
                        dest='sign', action='store', default=1)
    parser.add_argument('-l', '--lottery', help=u'指定更新彩种(可多选)，不选默认为所有彩种',
                        nargs='+')
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    if not args.cp:
        args.cp = ['ssq', 'dlt', 'pl3', 'pl5', 'qlc', 'qxc', '3d', 'sfc']
    if args.help:
        parser.print_help()
        print(u"\n示例")
