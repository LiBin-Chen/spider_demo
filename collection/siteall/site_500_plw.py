#! /usr/bin/python
# -*- coding: utf-8 -*-
from packages.siteall.check_list import get_expect

__author__ = 'snow'
__time__ = '2019/3/14'

import re
import argparse
import threading
from lxml import etree
import time
import json
import random
import logging
import requests
from packages import Util as util, db, yzwl

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

collection = db.mongo['pay_proxies']
default_headers = {
    'Host': 'kaijiang.500.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.local_yzwl
lock = threading.Lock()


def get_prolist(limit=10):
    """
    获取代理列表
    从url获取改为从数据库获取
    """
    res = requests.get('http://proxy.elecfans.net/proxys.php?key=nTAZhs5QxjCNwiZ6&num=10&type=pay'.format(limit))
    data = res.json()
    # data = collection.find({}).limit(limit)
    prolist = []
    for vo in data['data']:
        prolist.append(vo['ip'])
    _num = len(prolist)
    if _num <= 1:
        return None
    # print(_num, prolist)
    return [_num, prolist]


# prolist = []
# data = collection.find({}).limit(limit)
# for vo in data:
#     prolist.append(vo['ip'])
# _num = len(prolist)
# if _num <= 1:
#     return None
# # print(_num, prolist)
# return [_num, prolist]


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

        print('获取url： {0}'.format(url))
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=None)
        # print('rs', rs.text)

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
    rs.encoding = rs.apparent_encoding
    # print('kwargs', kwargs)
    with lock:
        return _parse_detail_data(rs.text, url=url, **kwargs)


# print('t', t)


def _parse_detail_data(data=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    data_item = {}
    db_name = kwargs.get('db_name', '')

    if not db_name:
        _logger.info('INFO: 请检查是否传入正确的数据库; URL:%s' % (url))
        return
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    # print('data', data)
    root = etree.HTML(data)
    open_xpath = root.xpath('//div[@class="ball_box01"]//text()')
    code_list = []
    for _code in open_xpath:
        _code = util.cleartext(_code)
        if not _code:
            continue
        code_list.append(_code)
    open_code = ','.join(code_list)
    roll = root.xpath('//span[@class="cfont1 "]//text()')
    currentAward = root.xpath('//span[@class="cfont1"]//text()')
    # print('currentAward',currentAward)
    # print('rool',roll)
    roll = util.cleartext(roll[0])
    currentAward = util.cleartext(currentAward[0]) if currentAward else 0
    expect_path = root.xpath('//font[@class="cfont2"]//text()')
    expect = '20' + util.cleartext(expect_path[0])
    date_xpath = root.xpath('//span[@class="span_right"]//text()')
    open_date = date_xpath[0].split(' ')[0].split('开奖日期：')[-1]

    year = open_date.split('年')[0]
    mon = open_date.split('年')[-1].split('月')[0]
    day = open_date.split('年')[-1].split('月')[-1].replace('日', '')
    mon = '0' + mon if len(mon) == 1 else mon
    day = '0' + day if len(day) == 1 else day

    open_time = year + '-' + mon + '-' + day + ' 20:30:00'
    tr_list = root.xpath('//table[@class="kj_tablelist02"]//tr[@align="center"]')
    data_item = {"rolling": "0", "bonusSituationDtoList": [
        {"winningConditions": "号码按位相符", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "直选"},
    ], "nationalSales": "0", "currentAward": "0"}
    data_item['nationalSales'] = util.modify_unit(roll)
    data_item['currentAward'] = util.modify_unit(currentAward)
    for tr in tr_list[2:4]:
        prize_name = tr.xpath('.//td[1]//text()')  # 2 3
        prize_number = tr.xpath('.//td[2]//text()')
        prize = tr.xpath('.//td[3]//text()')
        # print(prize_name)
        # print(prize)
        # print(prize_number)
        if prize_name[0] in ['排列5直选', '排列五直选']:
            try:
                # print(prize)
                # print(prize_number)
                data_item['bonusSituationDtoList'][0]['numberOfWinners'] = prize_number[0]
                data_item['bonusSituationDtoList'][0]['singleNoteBonus'] = prize[0]
            except:
                data_item['bonusSituationDtoList'][0]['numberOfWinners'] = 0
                data_item['bonusSituationDtoList'][0]['singleNoteBonus'] = 0
    else:
        pass

    data_item = json.dumps(data_item, ensure_ascii=True)
    item = {
        'open_result': data_item,
        'open_time': open_time,
    }

    # print('item', item)
    # print('不保存数据')
    try:
        save_data(url, db_name, open_code, expect, item)
    except:
        _logger.info('INFO: 数据存入错误; item: {0}'.format(item))


def parse_list(bonusSituationDtoList, data_list):
    if not data_list:
        return
    # print('data_list', data_list)
    item = {
    }
    # print('dlist', data_list)
    try:
        numberOfWinners = data_list[2] if len(data_list) >= 2 else 0
        singleNoteBonus = data_list[3] if len(data_list) >= 3 else 0
    except:
        numberOfWinners = 0
        singleNoteBonus = 0
    item['numberOfWinners'] = numberOfWinners
    item['singleNoteBonus'] = singleNoteBonus
    if '追加' in data_list:
        try:
            item['additionNumber'] = data_list[6] if len(data_list) >= 6 else 0
            item['additionBonus'] = data_list[7] if len(data_list) >= 7 else 0
        except:
            item['additionNumber'] = 0
            item['additionBonus'] = 0
    bonusSituationDtoList.append(item)


def parse_data(data, symol=1):
    data_list = []

    for _data in data:
        if symol == 1:
            _data = util.cleartext(_data)
        else:
            _data = int(util.number_format(util.cleartext(_data)))
        data_list.append(_data)

    return data_list


def save_data(url, db_name, open_code, expect, item):
    # print('item', item)
    # print('db_name', db_name)
    info = mysql.select(db_name, condition=[('expect', '=', expect)], limit=1)
    if not info:
        cp_id = open_code.replace(',', '')
        item['cp_id'] = cp_id
        item['cp_sn'] = '15' + str(expect)
        item['open_url'] = url
        item['open_code'] = open_code
        item['expect'] = expect
        item['create_time'] = util.date()
        # print('item', item)
        mysql.insert(db_name, data=item)
        _logger.info('INFO:数据保存成功, 期号%s ; URL:%s' % (expect, url))
    else:
        mysql.update(db_name, condition=[('expect', '=', expect)], data=item)
        _logger.info('INFO:数据已存在 作更新, 期号: %s ; URL:%s' % (expect, url))


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


def run(url, proxy, **kwargs):
    if url:
        result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)


def main(**kwargs):
    max_thread = 10
    task_list = []
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    interval = kwargs.get('interval', 10)
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    proxy = util.get_prolist(10)
    CP = {
        93: 'http://kaijiang.500.com/shtml/plw/19068.shtml',  # 14052后 就是改版后的页面
    }
    RESULT = {
        93: 'game_plw_result',
    }
    url = CP[93]
    dlt_list = get_expect('http://kaijiang.500.com/plw.shtml')
    for expect in dlt_list:
        lottery_result = RESULT[93]
        kwargs['db_name'] = lottery_result
        run(url, proxy, **kwargs)
        old_expect = url.split('/')[-1].split('.')[0]
        url = url.replace(old_expect, str(expect))
        time.sleep(2)


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    # parser.add_argument('-u', '--url', help=u'从检索结果的 URL 开始遍历下载产品数据',
    #                     dest='url', action='store', default=None)
    parser.add_argument('-sd', '--sd', help=u'从指定日期开始下载数据',
                        dest='sd', action='store', default='03/01/2019')
    parser.add_argument('-ed', '--ed', help=u'从指定日期结束下载数据',
                        dest='ed', action='store', default=None)
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
    cmd()
    # while 1:
    #     cmd()
    # time.sleep(60)
