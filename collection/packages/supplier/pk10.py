#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import time
import json
import random
import logging
import requests
import argparse
import threading
from lxml import etree
from packages import Util as util, yzwl

__author__ = 'snow'
'''程序

@description
    说明
'''

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

db = yzwl.DbSession()
collection = db.mongo['pay_proxies']
default_headers = {
    # 'Referer': '',
    # 'Host': 'http://zq.win007.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}
default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}


def fetch_data(url, proxy=None, headers=None, **kwargs):
    '''
    获取页面数据
    @description
        pk10网页采集


    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据
    '''

    # if isinstance(headers, dict):
    #     default_headers = headers
    try:
        proxy = 0
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}

        sess = requests.Session()
        # _logger.info('INFO:使用代理, %s ;' % (proxies))
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
        elif rs.status_code == 404:
            _logger.debug('STATUS:404 ; INFO:请求错误 ; URL:%s' % url)
            return 404
        _logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            rs.status_code, proxies['http'] if proxy else '', url))
        return -405
    rs.encoding = 'utf-8'
    return _parse_detail_data(rs.text, url=url, **kwargs)


def _parse_detail_data(data=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''

    abbreviation = kwargs.get('abbreviation', '')
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404

    root = etree.HTML(data)
    if abbreviation == 'gdklsf':
        abbreviation = 'gdkl10'
    parse_xpath = '//div[@data-type="{0}"]//tr'.format(abbreviation)
    tr_list = root.xpath(parse_xpath)

    if not tr_list:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    # tr_list = tr_list[:3] # 获取最新一天的数据，只拿更新一期的数据
    item_list = []
    for tr in tr_list:
        expect_xpath = tr.xpath('.//td[1]//text()')
        open_code = tr.xpath('.//td[2]/div[1]//span//text()')
        if not expect_xpath:
            continue
        expect_list = []
        for _expect in expect_xpath:
            _expect = util.cleartext(_expect)
            if _expect:
                expect_list.append(_expect)
        open_code_list = []
        for _code in open_code:
            _code = util.cleartext(_code)
            if _code:
                open_code_list.append(_code)
        open_code = ','.join(open_code_list)
        open_date = url.split('-')[-1].split('.')[0]
        expect = expect_list[0]
        open_time = open_date[:4] + '-' + open_date[4:6] + '-' + open_date[6:] + ' ' + expect_list[1]
        if 'toda' in open_time:
            open_time = util.date(format='%Y-%m-%d') + ' ' + open_time.split(' ')[-1]
            now_date = util.date(format='%Y-%m-%d %H:%M:%S')
            if open_time > now_date:
                open_time = str(datetime.date.today() - datetime.timedelta(days=1)) + ' ' + open_time.split(' ')[-1]

        item = {
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
            'source_sn': 16,
            'create_time': util.date(),
        }
        item_list.append(item)
        # print('item', item)
    # 只拿更新一期的数据
    return item_list[0]


def fetch_search_data(**kwargs):
    '''
    根据关键词抓取搜索数据
    '''
    pass


def fetch_search_list(**kwargs):
    '''
    抓取搜索列表数据
    '''
    data_dict = {
        'detail': [],
        'list': [],
        'url': []
    }
    fetch_search_data(**kwargs)
    return data_dict


def api_fetch_data(**kwargs):
    '''
    从接口获取数据
    '''
    pass


def fetch_update_data(url=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    url = kwargs.get('update_url')
    data = fetch_data(url, **kwargs)

    # 对每次返回的数据进行简单处理
    res = {}
    id = kwargs.get('id')
    if isinstance(data, dict):
        data['id'] = id
        data['lottery_type'] = kwargs.get('lottery_type')
        data['lottery_name'] = kwargs.get('lottery_name')
        data['lottery_result'] = kwargs.get('lottery_result')

        res['dlist'] = data
        res['status'] = 200

    else:
        res = kwargs  # 队列原的数据
        res['id'] = id
        res['status'] = data
        res['count'] = kwargs.get('count', 1)  # count 重试次数

    return res


if __name__ == '__main__':
    kwargs = {"id": 3, "abbreviation": "pk10", "lottery_name": "\u5317\u4eac\u8d5b\u8f66PK10",
              "lottery_type": "HIGH_RATE", "update_url": "https://www.pk10.me/draw-pk10-today.html",
              "lottery_result": "game_pk10_result"}
    url = kwargs.get('pks_open_url')
    print(fetch_update_data(url=None, **kwargs))
