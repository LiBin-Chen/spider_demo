#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import random
import logging
import requests
from lxml import etree

try:
    from packages import yzwl
    from packages import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.yzwl as yzwl
    import packages.Util as util

__author__ = 'snow'
'''
极速虎网封装函数    jsh365

@description
    收集更新彩票数据

'''

_logger = logging.getLogger('yzwl_spider')

default_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.jsh365.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
}


def fetch_data(url, proxy=None, headers=None, **kwargs):
    '''
    获取页面数据
    @description
        获取体育赛事数据


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

        rs = requests.get(url, headers=None, cookies=None, timeout=30)
        print('rs', rs.text)
    except Exception as e:
        # 将进行重试，可忽略
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    if rs.status_code != 200:
        if rs.status_code == 500 and 'Thank you for dropping by' in rs.text:
            _logger.debug('STATUS:-500 ; INFO:请求被禁止 ; PROXY：%s ; URL:%s ; User-Agent:%s' % (
                proxies['http'] if proxy else '', url, headers.get('user_agent', '')))
            return -500
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

    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    root = etree.HTML(data)
    li_list = root.xpath('//ul[@id="content"]//li')

    item_list = []
    for li in li_list:
        expect = li.xpath('.//h1//em[1]//text()')
        open_time = li.xpath('.//h1//em[2]//text()')
        open_code_list = li.xpath('.//p//span//text()')

        expect = util.cleartext(expect[0], '第', '期') if expect else ''
        if not expect:  # 如果期号为空 则不进行下一步
            continue
        if len(expect) == 10:
            expect = expect[:8] + '0' + expect[8:]
        open_time = util.cleartext(open_time[0]) if open_time else ''
        open_code = ','.join(open_code_list[:-1]) + '+' + open_code_list[-1]

        item = {
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
            'source_sn': 25,
            'create_time': util.date(),
        }
        item_list.append(item)

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
    #https://www.jsh365.com/award/dp-hbyzfcesxw/2019-04-18.html
    更新彩票的开奖结果

    @description
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
    kwargs = {"id": 34, "abbreviation": "bjkzc", "lottery_name": "\u5317\u4eac\u5feb\u4e2d\u5f69",
              "lottery_type": "HIGH_RATE", "update_url": "https://m.cjcp.com.cn/kaijiang/kj-kzc/",
              "lottery_result": "game_bjkzc_result"}
    fetch_update_data(**kwargs)
