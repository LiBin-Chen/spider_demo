#! /usr/bin/python
# -*- coding: utf-8 -*-


import time
import json
import random
import logging
import argparse
import requests
import threading
from lxml import etree

from packages import Util as util, yzwl

__author__ = 'snow'
__time__ = '2019/3/12'

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.yzwl
lock = threading.Lock()


# def get_prolist(limit=0):
#     """
#     获取代理列表
#     从url获取改为从数据库获取
#     """
#
#     prolist = []
#     data = collection.find({}).limit(limit)
#     for vo in data:
#         prolist.append(vo['ip'])
#     _num = len(prolist)
#     if _num <= 1:
#         return None
#     # print(_num, prolist)
#     return [_num, prolist]


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

        sess = requests.Session()
        # _logger.info('INFO:使用代理, %s ;' % (proxies))
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=proxies)
    except Exception as e:
        # 将进行重试，可忽略
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    if rs.status_code != 200:
        if rs.status_code == 500 and 'Thank you for dropping by' in rs.text:
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
    # print('kwargs', kwargs)
    with lock:
        return _parse_detail_data(rs.text, url=url, **kwargs)


def _parse_detail_data(data=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    db_name = kwargs.get('db_name', '')
    abbreviation = kwargs.get('abbreviation', '')
    if not db_name:
        _logger.info('INFO: 请检查是否传入正确的数据库; URL:%s' % (url))
        return
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    root = etree.HTML(data)
    parse_xpath = '//div[@data-type="{0}"]//tr'.format(abbreviation)
    tr_list = root.xpath(parse_xpath)
    if not tr_list:
        _logger.info('INFO: 该日期没有获取到数据; URL:%s' % (url))
        return
    # print('tr_list', tr_list)
    # print('tr_list', len(tr_list))
    # tr_list = reversed(tr_list)

    for tr in tr_list:
        expect_xpath = tr.xpath('.//td[1]//text()')
        open_code = tr.xpath('.//td[2]/div[1]//span//text()')
        if not expect_xpath:
            # print('空...')
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
        print('*' * 100)
        cp_id = open_code.replace(',', '')  # 以中奖号+作为唯一id 并且开奖时间间隔大于15分钟  高频彩最低为20分钟，连着开同号概率极小
        cp_sn = int(str(16) + expect)
        item = {
            'cp_id': cp_id,
            'cp_sn': cp_sn,
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
            'create_time': util.date(),
        }
        # print('item', item)
        # [('id','>','10'),|,('status',1)]
        info = mysql.select(db_name, condition=[('expect', '=', expect)], limit=1)
        if not info:
            mysql.insert(db_name, data=item)
            _logger.info('INFO:数据保存成功, 期号%s ; URL:%s' % (expect, url))
        else:
            _logger.info('INFO:数据已存在不做重复存入, 期号: %s ; URL:%s' % (expect, url))


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    '''
    根据关键词抓取搜索数据
    '''
    if keyword:
        print('正在获取关键词：%s 的相关数据' % keyword)
        keyword = keyword.replace('*', '')
        url = ''
    elif 'url' in kwargs:
        url = kwargs['url']
    else:
        return
    try:
        proxies = None
        if proxy:
            proxies = {'http': 'http://{0}'.format(random.choice(proxy[1]))}
        rs = requests.get(url, headers=default_headers, cookies=_cookies, timeout=20, proxies=proxies)
    except Exception as e:
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        if 'Invalid URL' not in str(e):
            data_dict['list'].append({'status': -400, 'url': url, 'id': id, 'count': kwargs.get('count', 1)})
        return -400

    if rs.status_code not in (200, 301, 302):
        if rs.status_code == 500 and 'Thank you for dropping by' in rs.text:
            _logger.debug('STATUS:-500 ; INFO:请求被禁止 ; PROXY：%s ; URL:%s ; User-Agent:%s' % (
                proxies['http'] if proxy else '', url, headers.get('user_agent', '')))
            data_dict['url'].append({'status': -500, 'url': url, 'id': id})
            return -500
        _logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            rs.status_code, proxies['http'] if proxy else '', url))
        data_dict['list'].append({'status': -405, 'url': url, 'id': id, 'count': kwargs.get('count', 1)})
        return -405

    # 强制utf-8
    rs.encoding = 'utf-8'
    return 200


def fetch_search_list(url, id=None, headers=None, proxy=None, **kwargs):
    '''
    抓取搜索列表数据
    '''
    data_dict = {
        'detail': [],
        'list': [],
        'url': []
    }
    fetch_search_data(id=id, data_dict=data_dict, headers=headers, proxy=proxy, url=url, **kwargs)
    return data_dict


def api_fetch_data(goods_sn=None, keyword=None, proxy=None, numofresult=1, **kwargs):
    '''
    从接口获取数据
    '''
    proxies = kwargs.get('proxies')
    if proxies is None and proxy:
        i = random.randint(0, proxy[0] - 1)
        proxies = {
            'http': 'http://' + proxy[1][i],
            'https': 'http://' + proxy[1][i]
        }

    api_url = ''
    if not api_url:
        return None
    parm_data = {
    }
    sess = requests.Session()
    headers = default_headers.copy()
    headers['Host'] = ''
    try:
        res = sess.get(url=api_url, headers=headers, params=parm_data, proxies=proxies)
    except requests.RequestException as e:
        print('从接口获取数据失败')
        return -1
    data = json.loads(res.content)
    '''
    接口数据解析
    '''
    return data


def fetch_update_data(url=None, id=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    headers = kwargs.get('headers')
    proxy = kwargs.get('proxy')
    expect = kwargs.get('expect')  # 最新的期数
    open_time = kwargs.get('open_time')  # 最新的开奖时间，如果是第一期，则由上期作为识别
    open_url = kwargs.get('open_url')  # 同上
    provider_name = kwargs.get('provider_name')
    hot_update = kwargs.get('hot_update', False)
    kw = kwargs.get('kw', '')
    return


def run(lottery_chart_url, dlist, **kwargs):
    proxy = kwargs.get('proxy', '')
    hs = kwargs.get('hs', '')

    if not hs:
        '下载历史数据'
        result = fetch_data(url=lottery_chart_url, proxy=proxy, headers=default_headers, **kwargs)
    else:
        for str_time in dlist:
            str_time = ''.join(str_time.split('-'))
            url = lottery_chart_url.replace('today', str_time)
            result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)


def main(**kwargs):
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    interval = kwargs.get('interval', 0)
    dlist = util.specified_date(sd, ed)

    sql_data = mysql.select('t_lottery_pks',
                            fields=('abbreviation', 'lottery_name', 'lottery_result', 'lottery_chart_url'))
    task_list = []
    max_thread = 3
    for _data in sql_data:
        if _data['lottery_name'] not in ['北京赛车PK10', '重庆时时彩', '天津时时彩', '江苏快三', '新疆时时彩', '广东快乐十分']:
            # print('非所需彩种，忽略..')
            continue

        lottery_chart_url = _data.get('lottery_chart_url')
        kwargs = {
            'db_name': _data.get('lottery_result'),
            'abbreviation': _data.get('abbreviation'),
            'hs': kwargs['hs']
        }

        task = threading.Thread(target=run, args=(lottery_chart_url, dlist), kwargs=kwargs,
                                name="thread_{0}".format(len(task_list)))
        task.start()
        task_list.append(task)
        if len(task_list) >= max_thread:
            for task in task_list:
                task.join()
            task_list = []


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-sd', '--sd', help=u'从指定日期开始下载数据',
                        dest='sd', action='store', default='03/17/2019')
    parser.add_argument('-ed', '--ed', help=u'从指定日期结束下载数据',
                        dest='ed', action='store', default=None)
    parser.add_argument('-hs', '--hs', help=u'是否是下载历史数据',
                        dest='hs', action='store', default=1)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    if args.help:
        parser.print_help()
        # print(u"\n示例")
    elif args.sd:
        main(**args.__dict__)
    else:
        main()


if __name__ == '__main__':

    while 1:
        cmd()
        print('waiting ...')
        time.sleep(480)
