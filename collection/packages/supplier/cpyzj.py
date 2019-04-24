#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import random
import logging
import execjs
import requests
from lxml import etree
from packages import Util as util, Util

__author__ = 'snow'
'''程序

@description
    说明
'''

_logger = logging.getLogger('yzwl_spider')

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}


def get_sign(key):
    '''
    调用js生成请求参数sign
    :param key:
    :return:
    '''
    # 可增加动态获取文件地址的工具方法
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")) + '/static/js/md5.js') as f:
        js_data = f.read()
    ctx = execjs.compile(js_data)
    sign = ctx.call('md5', key)
    return sign


def fetch_data(url, headers=None, **kwargs):
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
        rs = sess.get(url, headers=default_headers, cookies=None, timeout=30, proxies=proxies)
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
    # print('parse_xpath', parse_xpath)
    tr_list = root.xpath(parse_xpath)

    if not tr_list:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
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
        cp_id = open_code.replace(',', '')  # 以中奖号+作为唯一id 并且开奖时间间隔大于15分钟  高频彩最低为20分钟，连着开同号概率极小
        cp_sn = int(str(16) + expect)
        item = {
            # 'cp_id': cp_id,
            # 'cp_sn': cp_sn,
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
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


def api_fetch_data(lotto_code, **kwargs):
    '''
    从接口获取数据
    '''
    url = 'https://www.cpyzj.com/req/cpyzj/lotHistory/queryNewestLotByCode'  # 接口url
    open_url = 'https://www.cpyzj.com/open-awards-detail.html?lotCode={}&lotGroupCode=1'.format(
        lotto_code)  # 页面url
    timestamp = int(time.time())
    key = 'lotCode={}&lotGroupCode={}&timestamp={}&token=noget&key=cC0mEYrCmWTNdr1BW1plT6GZoWdls9b&'.format(lotto_code,
                                                                                                            0,
                                                                                                            timestamp)
    headers = kwargs.get('headers')
    if isinstance(headers, dict):
        default_headers = headers
    try:
        proxy = 0
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}

        sign = get_sign(key)
        form_data = {
            'token': 'noget',
            'timestamp': timestamp,
            'lotGroupCode': '0',
            'lotCode': lotto_code,
            'sign': sign.upper(),
        }

        session = requests.Session()
        res = session.post(url, data=form_data)
    except Exception as e:
        # 将进行重试，可忽略
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    if res.status_code != 200:
        if res.status_code == 500:
            _logger.debug('STATUS:-500 ; INFO:请求被禁止 ; PROXY：%s ; URL:%s ; User-Agent:%s' % (
                proxies['http'] if proxy else '', url, headers.get('user_agent', '')))
            return -500
        elif res.status_code == 404:
            _logger.debug('STATUS:404 ; INFO:请求错误 ; URL:%s' % url)
            return 404
        _logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            res.status_code, proxies['http'] if proxy else '', url))
        return -405

    try:
        data = res.json()
        issue = data['data']['preDrawIssue']
        open_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['data']['preDrawTime'] / 1000))
        open_code = data['data']['preDrawCode']

        item = {
            'expect': issue,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': open_url,
            'source_sn': 18,
            'create_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        return item
    except Exception as e:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404


def fetch_update_data(url=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    url = kwargs.get('update_url', '')
    if 'lotCode' in url:  # 再加上一个使用的判断条件
        # 接口更新
        lotto_code = url.split('lotCode=')[-1].split('&')[0]
        data = api_fetch_data(lotto_code, **kwargs)
    else:
        # 页面更新
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
    kwargs = {'id': 87, 'abbreviation': 'jssyxw', 'lottery_name': '11选5', 'lottery_type': 'HIGH_RATE',
              'update_url': 'https://www.cpyzj.com/open-awards-detail.html?lotCode=10016&lotGroupCode=1',
              'lottery_result': 'game_jssyxw_result', 'headers': {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'},
              'proxy': None}
    # print(fetch_update_data(url=None, **kwargs))
