#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import random
import logging
import argparse
import requests
import threading
from lxml import etree

try:
    from packages import yzwl
    import packages.Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.yzwl as yzwl
    from packages import Util as util


'''requests整站爬虫

@description
    适用于层级较浅的网站
'''

_logger = logging.getLogger('demo_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.yzwl


def save_data(url, db_name, item):
    '''
    数据保存
    '''
    info = None
    if not info:
        item['create_time'] = util.date()
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ; URL:%s' % (db_name, item['demo'], url))

    else:
        item['update_time'] = util.date()
        del item['open_time']
        del item['create_time']
        mysql.update(db_name, condition=[('demo', '=', item['demo'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在 更新成功, 期号: %s ; URL:%s' % (db_name, item['demo'], url))


def fetch_data(url, proxy=None, headers=None, **kwargs):
    '''
    获取页面数据
    @description

    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据
    '''

    if isinstance(headers, dict):
        default_headers = headers
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}

        sess = requests.Session()
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=proxies)
    except Exception as e:
        # 将进行重试，可忽略
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    if rs.status_code != 200:
        if rs.status_code == 500:
            _logger.debug('STATUS:-500 ; INFO:请求被禁止 ; PROXY：%s ; URL:%s ; User-Agent:%s' % (
                proxies['http'] if proxy else '', url, headers.get('user_agent', '')))
            return -500
        # 已失效产品（url不存在）
        elif rs.status_code == 404:
            _logger.debug('STATUS:404 ; INFO:请求错误 ; URL:%s' % url)
            return 404
        _logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            rs.status_code, proxies['http'] if proxy else '', url))
        return -405
    # 强制utf-8
    rs.encoding = 'utf-8'

    return _parse_detail_data(rs.text, url=url, **kwargs)


def _parse_detail_data(data=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    '''
    页面数据解析
    '''
    save_data()


def fetch_search_data(**kwargs):
    '''
    根据关键词抓取搜索数据
    '''
    pass


def fetch_search_list(**kwargs):
    '''
    抓取搜索列表数据
    '''
    pass


def api_fetch_data(**kwargs):
    '''
    从接口获取数据
    '''
    pass


def fetch_update_data(url=None, id=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    pass


def main(**kwargs):
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    interval = kwargs.get('interval', 60)
    date_list = util.specified_date(sd, ed)

    data = [{'url': '1'}, {'url': '2'}]
    while 1:
        proxy = util.get_prolist(10)
        for _data in data:
            url = _data.get('url', '')
            if not url:
                continue
            fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)

            '''
            #根据url规律进行控制
            '''
            for str_time in date_list:
                pass

        if not interval:
            break
        print('-------------- sleep %s sec -------------' % interval)
        time.sleep(interval)


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-p', '--past', help=u'默认最新一期数据',
                        dest='past', action='store', default=1)
    parser.add_argument('-sd', '--sd', help=u'从指定日期开始下载数据',
                        dest='sd', action='store', default='04/28/2019')
    parser.add_argument('-ed', '--ed', help=u'从指定日期结束下载数据',
                        dest='ed', action='store', default=None)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    if args.help:
        parser.print_help()
        print(u"\n示例")
    elif args.sd:
        main(**args.__dict__)
    else:
        main()


if __name__ == '__main__':
    cmd()
