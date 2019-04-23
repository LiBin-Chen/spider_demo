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

        rs = requests.get(url, headers=default_headers, cookies=None, timeout=30)
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
    lotto_type = url.split('-')[0].split('/')[-1]
    if lotto_type == 'gp':
        parse_xpath = {
            'root_xpath': '//table[@class="_tab"]//tr',  # table 列表
            'date_xpath': '//div[@class="_p2"]//text()',  # 高频开奖日期
            'latest_xpath': '//table[@class="_tab"]//tr//td[3]//text()',  # 最新一次开奖
            'expect_xpath': './/td[1]//text()',  # 期号
            'time_xpath': './/td[2]//text()',  # 开奖时间
            'code_xpath': './/td[3]//text()',  # 开奖结果
        }

    elif lotto_type == 'dp':
        parse_xpath = {
            'root_xpath': '//table[@class="_tab _tab2"]//tr',  # table 列表
            'date_xpath': '//span[@class="_time"]//text()',  # 低频开奖日期
            'latest_xpath': '//div[@class="_p2"]//div[@class="_balls"]//text()',  # 最新一次开奖
            'expect_xpath': './/td[1]//text()',  # 期号
            'time_xpath': './/td[3]//text()',  # 开奖时间
            'code_xpath': './/td[2]//text()',  # 开奖结果
        }
    else:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404

    root = etree.HTML(data)
    date_xpath = root.xpath(parse_xpath['date_xpath'])  # 判断日期是否是当天日期
    if not date_xpath:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404

    today = str(int(util.number_format(util.cleartext(date_xpath[0], ':', '-', '年', '月', '日'))))  # 转成整数进行对比
    use_date = today[:4] + '-' + today[4:6] + '-' + today[6:] + ' '
    tr_list = root.xpath(parse_xpath['root_xpath'])
    if not tr_list:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    item_list = []
    for tr in tr_list:
        expect_xpath = tr.xpath(parse_xpath['expect_xpath'])
        time_xpath = tr.xpath(parse_xpath['time_xpath'])
        code_xpath = tr.xpath(parse_xpath['code_xpath'])
        if not expect_xpath:
            continue
        '以中奖号+作为唯一id  各个网站+期号 作为 数据来源的标识 '

        code_list = []
        for _code in code_xpath:
            _code = util.cleartext(_code)
            if not _code:
                continue
            code_list.append(_code)

        expect = util.cleartext(use_date, '-') + expect_xpath[1] if lotto_type == 'gp' else util.cleartext(
            expect_xpath[0], '期')

        open_code = ','.join(code_list)
        if lotto_type == 'gp':
            open_time = use_date + time_xpath[0] if ':' in time_xpath[0] else use_date
        else:
            open_time = expect[:4] + '-' + time_xpath[0]
        create_time = util.date()
        item = {
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
            'source_sn': 11,
            'create_time': create_time,
        }
        item_list.append(item)
    # print('item', item_list[0])
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
    kwargs = {'abbreviation': 'gssyxw', 'lottery_name': '11选5', 'lottery_type': 'HIGH_RATE',
              'update_url': 'https://www.jsh365.com/award/gp-sxsyxw.html', 'lottery_result': 'game_gssyxw_result',
              'headers': {
                  'user-agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) '},
              'proxy': None, 'id': None, 'status': None, 'count': 1}
    fetch_update_data(**kwargs)
