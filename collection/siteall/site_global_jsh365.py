# ! /usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'snow'
__time__ = '2019/3/7'

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

'''
极速虎网封装函数    jsh365

@description
    收集彩票数据

'''

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

collection = db.mongo['pay_proxies']
default_headers = {
    # 'Referer': '',
    # 'Host': 'http://zq.win007.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.local_yzwl
lock = threading.Lock()


def get_prolist(limit=0):
    """
    获取代理列表
    从url获取改为从数据库获取
    """

    prolist = []
    data = collection.find({}).limit(limit)
    for vo in data:
        prolist.append(vo['ip'])
    _num = len(prolist)
    if _num <= 1:
        return None
    # print(_num, prolist)
    return [_num, prolist]


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
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=proxies)
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

    if not db_name:
        _logger.info('INFO: 请检查是否传入正确的数据库; URL:%s' % (url))
        return
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    # print('data',data)
    root = etree.HTML(data)
    url_type = kwargs.get('url_type')
    print('url_type', url_type)
    if url_type == 89:
        tr_list = root.xpath('//div[@class="tablebox ssqtable"]//table//tr')
        if not tr_list:
            _logger.info('INFO: 该日期没有获取到数据; URL:%s' % (url))
            return

        # tr_list = reversed(tr_list)
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')
            test_code = tr.xpath('.//td[4]//text()')
            test_open_code = tr.xpath('.//td[5]//text()')
            sales_count = tr.xpath('.//td[6]//text()')
            direct_election_number = tr.xpath('.//td[7]//text()')
            direct_election = tr.xpath('.//td[8]//text()')
            group_three_number = tr.xpath('.//td[9]//text()')
            group_three = tr.xpath('.//td[10]//text()')
            group_six_number = tr.xpath('.//td[11]//text()')
            group_six = tr.xpath('.//td[12]//text()')
            test_code = test_code[0] if test_code else 0
            test_open_code = test_open_code[0].replace(' ', ',') if test_open_code else 0
            sales_count = int(util.number_format(sales_count[0])) if sales_count else 0
            direct_election = direct_election[0] if direct_election else 0
            direct_election_number = direct_election[0] if direct_election and direct_election_number[
                0] != '-' else 0
            group_three = group_three[0] if group_three else 0
            group_three_number = group_three_number[0] if group_three_number and group_three_number[0] != '-' else 0
            group_six = group_six[0] if group_six else 0
            group_six_number = group_six_number[0] if group_six_number and group_six_number[0] != '-' else 0

            # group_six=tr.xpath('.//td[9]//text()')
            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            lottery_trend_result = ''
            open_result = {
                'direct_election': {'num': direct_election_number, 'amount': direct_election},
                'group_three': {'num': group_three_number, 'amount': group_three},
                'group_six': {'num': group_six, 'amount': group_six_number},
            }
            # open_result={"bonusSituationDtoList": [
            #     {"winningConditions": "三个号码相同", "numberOfWinners": "73519", "singleNoteBonus": "1,040", "prize": "一等奖"},
            #     {"prize": "二等奖"}], "nationalSales": "3826.22万", "currentAward": "0"}
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'open_url': url,
                'lottery_trend_result': lottery_trend_result,
                'test_machine_number': test_code,
                'open_machine_number': test_open_code,
                'bet_amount': sales_count,
                'open_result': open_result,
                'create_time': util.date(),
            }

            save_data(url, db_name, expect, item)

    elif url_type == 90:
        tr_list = root.xpath('//div[@class="tablebox qlctable"]//table//tr')
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')

            first_prize_num = tr.xpath('.//td[4]//text()')
            first_prize = tr.xpath('.//td[5]//text()')
            sales_count = 0
            second_prize_num = tr.xpath('.//td[4]//text()')
            second_prize = tr.xpath('.//td[5]//text()')

            third_prize_num = tr.xpath('.//td[6]//text()')
            third_prize = tr.xpath('.//td[7]//text()')

            fourth_prize_num = tr.xpath('.//td[8]//text()')
            fourth_prize = tr.xpath('.//td[9]//text()')

            fifth_prize_num = tr.xpath('.//td[10]//text()')
            fifth_prize = tr.xpath('.//td[11]//text()')

            sixth_prize_num = tr.xpath('.//td[12]//text()')
            sixth_prize = tr.xpath('.//td[13]//text()')

            seventh_prize_num = tr.xpath('.//td[14]//text()')
            seventh_prize = tr.xpath('.//td[15]//text()')

            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            first_prize = util.number_format(first_prize[0]) if first_prize else 0
            first_prize_num = util.number_format(first_prize_num[0]) if first_prize_num else 0
            second_prize = util.number_format(second_prize[0]) if second_prize else 0
            second_prize_num = util.number_format(second_prize_num[0]) if second_prize_num else 0
            third_prize = util.number_format(third_prize[0]) if third_prize else 0
            third_prize_num = util.number_format(third_prize_num[0]) if third_prize_num else 0
            fourth_prize = util.number_format(fourth_prize[0]) if fourth_prize else 0
            fourth_prize_num = util.number_format(fourth_prize_num[0]) if fourth_prize_num else 0
            fifth_prize = util.number_format(fifth_prize[0]) if fifth_prize else 0
            fifth_prize_num = util.number_format(fifth_prize_num[0]) if fifth_prize_num else 0
            sixth_prize = util.number_format(sixth_prize[0]) if sixth_prize else 0
            sixth_prize_num = util.number_format(sixth_prize_num[0]) if sixth_prize_num else 0
            seventh_prize = util.number_format(seventh_prize[0]) if seventh_prize else 0
            seventh_prize_num = util.number_format(seventh_prize_num[0]) if seventh_prize_num else 0

            open_result = {
                'first_prize': {'num': first_prize_num, 'amount': first_prize},
                'second_prize': {'num': second_prize_num, 'amount': second_prize},
                'third_prize': {'num': third_prize_num, 'amount': third_prize},
                'fourth_prize': {'num': fourth_prize_num, 'amount': fourth_prize},
                'fifth_prize': {'num': fifth_prize_num, 'amount': fifth_prize},
                'sixth_prize': {'num': sixth_prize_num, 'amount': sixth_prize},
                'seventh_prize': {'num': seventh_prize_num, 'amount': seventh_prize},
            }
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'bet_amount': sales_count,
                'open_result': open_result,
            }

            print('item', item)
            save_data(url, db_name, expect, item)
            # print('*' * 100)
    elif url_type == 91:
        tr_list = root.xpath('//div[@class="tablebox ssqtable"]//table//tr')
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')

            sales_count = tr.xpath('.//td[4]//text()')

            first_prize_num = tr.xpath('.//td[5]//text()')
            first_prize = tr.xpath('.//td[6]//text()')

            second_prize_num = tr.xpath('.//td[7]//text()')
            second_prize = tr.xpath('.//td[8]//text()')

            third_prize_num = tr.xpath('.//td[9]//text()')
            third_prize = tr.xpath('.//td[10]//text()')

            fourth_prize_num = tr.xpath('.//td[11]//text()')
            fourth_prize = tr.xpath('.//td[12]//text()')

            fifth_prize_num = tr.xpath('.//td[13]//text()')
            fifth_prize = tr.xpath('.//td[14]//text()')

            sixth_prize_num = tr.xpath('.//td[15]//text()')
            sixth_prize = tr.xpath('.//td[16]//text()')


            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            sales_count = util.number_format(sales_count[0]) if sales_count else 0

            first_prize = util.number_format(first_prize[0]) if first_prize else 0
            first_prize_num = util.number_format(first_prize_num[0]) if first_prize_num else 0
            second_prize = util.number_format(second_prize[0]) if second_prize else 0
            second_prize_num = util.number_format(second_prize_num[0]) if second_prize_num else 0
            third_prize = util.number_format(third_prize[0]) if third_prize else 0
            third_prize_num = util.number_format(third_prize_num[0]) if third_prize_num else 0
            fourth_prize = util.number_format(fourth_prize[0]) if fourth_prize else 0
            fourth_prize_num = util.number_format(fourth_prize_num[0]) if fourth_prize_num else 0
            fifth_prize = util.number_format(fifth_prize[0]) if fifth_prize else 0
            fifth_prize_num = util.number_format(fifth_prize_num[0]) if fifth_prize_num else 0
            sixth_prize = util.number_format(sixth_prize[0]) if sixth_prize else 0
            sixth_prize_num = util.number_format(sixth_prize_num[0]) if sixth_prize_num else 0
            # seventh_prize = util.number_format(seventh_prize[0]) if seventh_prize else 0
            # seventh_prize_num = util.number_format(seventh_prize_num[0]) if seventh_prize_num else 0
            open_result = {
                'first_prize': {'num': first_prize_num, 'amount': first_prize},
                'second_prize': {'num': second_prize_num, 'amount': second_prize},
                'third_prize': {'num': third_prize_num, 'amount': third_prize},
                'fourth_prize': {'num': fourth_prize_num, 'amount': fourth_prize},
                'fifth_prize': {'num': fifth_prize_num, 'amount': fifth_prize},
                'sixth_prize': {'num': sixth_prize_num, 'amount': sixth_prize},
            }
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'bet_amount': sales_count,
                'open_result':open_result,
                'create_time': util.date(),
            }
            save_data(url, db_name, expect, item)
            # print('item', item)
            # print('*' * 100)
    elif url_type == 92:
        tr_list = root.xpath('//div[@class="tablebox ssqtable"]//table//tr')
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')

            sales_count = tr.xpath('.//td[4]//text()')

            first_prize_num = tr.xpath('.//td[5]//text()')
            first_prize = tr.xpath('.//td[6]//text()')

            second_prize_num = tr.xpath('.//td[7]//text()')
            second_prize = tr.xpath('.//td[8]//text()')

            third_prize_num = tr.xpath('.//td[9]//text()')
            third_prize = tr.xpath('.//td[10]//text()')

            fourth_prize_num = tr.xpath('.//td[11]//text()')
            fourth_prize = tr.xpath('.//td[12]//text()')

            fifth_prize_num = tr.xpath('.//td[13]//text()')
            fifth_prize = tr.xpath('.//td[14]//text()')

            sixth_prize_num = tr.xpath('.//td[15]//text()')
            sixth_prize = tr.xpath('.//td[16]//text()')

            # seventh_prize_num = tr.xpath('.//td[14]//text()')
            # seventh_prize = tr.xpath('.//td[15]//text()')

            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            sales_count = util.number_format(sales_count[0]) if sales_count else 0

            first_prize = util.number_format(first_prize[0]) if first_prize else 0
            first_prize_num = util.number_format(first_prize_num[0]) if first_prize_num else 0
            second_prize = util.number_format(second_prize[0]) if second_prize else 0
            second_prize_num = util.number_format(second_prize_num[0]) if second_prize_num else 0
            third_prize = util.number_format(third_prize[0]) if third_prize else 0
            third_prize_num = util.number_format(third_prize_num[0]) if third_prize_num else 0
            fourth_prize = util.number_format(fourth_prize[0]) if fourth_prize else 0
            fourth_prize_num = util.number_format(fourth_prize_num[0]) if fourth_prize_num else 0
            fifth_prize = util.number_format(fifth_prize[0]) if fifth_prize else 0
            fifth_prize_num = util.number_format(fifth_prize_num[0]) if fifth_prize_num else 0
            sixth_prize = util.number_format(sixth_prize[0]) if sixth_prize else 0
            sixth_prize_num = util.number_format(sixth_prize_num[0]) if sixth_prize_num else 0
            open_result = {
                'first_prize': {'num': first_prize_num, 'amount': first_prize},
                'second_prize': {'num': second_prize_num, 'amount': second_prize},
                'third_prize': {'num': third_prize_num, 'amount': third_prize},
                'fourth_prize': {'num': fourth_prize_num, 'amount': fourth_prize},
                'fifth_prize': {'num': fifth_prize_num, 'amount': fifth_prize},
                'sixth_prize': {'num': sixth_prize_num, 'amount': sixth_prize},
            }
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'bet_amount': sales_count,
                'open_result': open_result,
                'create_time': util.date(),
            }
            save_data(url, db_name, expect, item)

    elif url_type == 93:
        tr_list = root.xpath('//div[@class="tablebox qxctable"]//table//tr')
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')
            sales_count = tr.xpath('.//td[4]//text()')
            first_prize_num = tr.xpath('.//td[5]//text()')
            first_prize = tr.xpath('.//td[6]//text()')
            second_prize_num = tr.xpath('.//td[7]//text()')
            second_prize = tr.xpath('.//td[8]//text()')
            third_prize_num = tr.xpath('.//td[9]//text()')
            third_prize = tr.xpath('.//td[10]//text()')

            fourth_prize_num = tr.xpath('.//td[11]//text()')
            fourth_prize = tr.xpath('.//td[12]//text()')

            fifth_prize_num = tr.xpath('.//td[13]//text()')
            fifth_prize = tr.xpath('.//td[14]//text()')

            sixth_prize_num = tr.xpath('.//td[15]//text()')
            sixth_prize = tr.xpath('.//td[16]//text()')


            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            sales_count = util.number_format(sales_count[0]) if sales_count else 0

            first_prize = util.number_format(first_prize[0]) if first_prize else 0
            first_prize_num = util.number_format(first_prize_num[0]) if first_prize_num else 0
            second_prize = util.number_format(second_prize[0]) if second_prize else 0
            second_prize_num = util.number_format(second_prize_num[0]) if second_prize_num else 0
            third_prize = util.number_format(third_prize[0]) if third_prize else 0
            third_prize_num = util.number_format(third_prize_num[0]) if third_prize_num else 0
            fourth_prize = util.number_format(fourth_prize[0]) if fourth_prize else 0
            fourth_prize_num = util.number_format(fourth_prize_num[0]) if fourth_prize_num else 0
            fifth_prize = util.number_format(fifth_prize[0]) if fifth_prize else 0
            fifth_prize_num = util.number_format(fifth_prize_num[0]) if fifth_prize_num else 0
            sixth_prize = util.number_format(sixth_prize[0]) if sixth_prize else 0
            sixth_prize_num = util.number_format(sixth_prize_num[0]) if sixth_prize_num else 0
            open_result = {
                'first_prize': {'num': first_prize_num, 'amount': first_prize},
                'second_prize': {'num': second_prize_num, 'amount': second_prize},
                'third_prize': {'num': third_prize_num, 'amount': third_prize},
                'fourth_prize': {'num': fourth_prize_num, 'amount': fourth_prize},
                'fifth_prize': {'num': fifth_prize_num, 'amount': fifth_prize},
                'sixth_prize': {'num': sixth_prize_num, 'amount': sixth_prize},
            }
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'open_url': url,
                'bet_amount': sales_count,
                'open_result': open_result,
                'create_time': util.date(),

            }
            save_data(url, db_name, expect, item)
            # print('item', item)
            # print('*' * 100)

            # save_data(url, db_name, expect, item)
    elif url_type == 94:
        tr_list = root.xpath('//div[@class="tablebox ssqtable"]//table//tr')
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')

            test_code = ''
            sales_count = tr.xpath('.//td[5]//text()')

            first_prize_num = tr.xpath('.//td[6]//text()')
            first_prize = tr.xpath('.//td[7]//text()')

            second_prize_num = tr.xpath('.//td[8]//text()')
            second_prize = tr.xpath('.//td[9]//text()')

            third_prize_num = tr.xpath('.//td[10]//text()')
            third_prize = tr.xpath('.//td[11]//text()')

            fourth_prize_num = tr.xpath('.//td[12]//text()')
            fourth_prize = tr.xpath('.//td[13]//text()')

            fifth_prize_num = tr.xpath('.//td[14]//text()')
            fifth_prize = tr.xpath('.//td[15]//text()')

            sixth_prize_num = tr.xpath('.//td[16]//text()')
            sixth_prize = tr.xpath('.//td[17]//text()')

            # seventh_prize_num = tr.xpath('.//td[14]//text()')
            # seventh_prize = tr.xpath('.//td[15]//text()')

            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            sales_count = util.number_format(sales_count[0]) if sales_count else 0

            first_prize = util.number_format(first_prize[0]) if first_prize else 0
            first_prize_num = util.number_format(first_prize_num[0]) if first_prize_num else 0
            second_prize = util.number_format(second_prize[0]) if second_prize else 0
            second_prize_num = util.number_format(second_prize_num[0]) if second_prize_num else 0
            third_prize = util.number_format(third_prize[0]) if third_prize else 0
            third_prize_num = util.number_format(third_prize_num[0]) if third_prize_num else 0

            open_result = {
                'direct_election': {'num': first_prize_num, 'amount': first_prize},
                'group_three': {'num': second_prize_num, 'amount': second_prize},
                'group_six': {'num': third_prize_num, 'amount': third_prize},
            }
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'test_machine_number': '',
                'bet_amount': sales_count,
                'open_result': open_result,
                'create_time': util.date(),
                # 'seventh_prize': {'num': seventh_prize_num, 'amount': seventh_prize},
            }

            # print('item', item)
            # print('db_name', db_name)
            save_data(url, db_name, expect, item)
            # print('*' * 100)

        # save_data(url, db_name, expect, item)
    elif url_type == 95:
        tr_list = root.xpath('//div[@class="tablebox qxctable"]//table//tr')
        for tr in tr_list[2:]:
            expect = tr.xpath('.//td[1]//text()')
            open_time = tr.xpath('.//td[2]//text()')
            open_code = tr.xpath('.//td[3]//text()')

            test_code = tr.xpath('.//td[4]//text()')
            sales_count = tr.xpath('.//td[5]//text()')

            first_prize_num = tr.xpath('.//td[6]//text()')
            first_prize = tr.xpath('.//td[7]//text()')

            second_prize_num = tr.xpath('.//td[8]//text()')
            second_prize = tr.xpath('.//td[9]//text()')

            third_prize_num = tr.xpath('.//td[10]//text()')
            third_prize = tr.xpath('.//td[11]//text()')

            fourth_prize_num = tr.xpath('.//td[12]//text()')
            fourth_prize = tr.xpath('.//td[13]//text()')

            fifth_prize_num = tr.xpath('.//td[14]//text()')
            fifth_prize = tr.xpath('.//td[15]//text()')

            sixth_prize_num = tr.xpath('.//td[16]//text()')
            sixth_prize = tr.xpath('.//td[17]//text()')

            seventh_prize_num = tr.xpath('.//td[18]//text()')
            seventh_prize = tr.xpath('.//td[19]//text()')

            if not expect:
                print('expect', expect)
                continue
            expect = util.number_format(expect[0])
            if not isinstance(expect, float):
                print('expect', expect)
                continue
            expect = int(expect)
            open_time = open_time[0].split('(')[0]
            open_code_list = []
            for _code in open_code:
                _code = util.cleartext(_code)
                if _code:
                    open_code_list.append(_code)

            open_code = ','.join(open_code_list)

            sales_count = util.number_format(sales_count[0]) if sales_count else 0

            first_prize = util.number_format(first_prize[0]) if first_prize else 0
            first_prize_num = util.number_format(first_prize_num[0]) if first_prize_num else 0
            second_prize = util.number_format(second_prize[0]) if second_prize else 0
            second_prize_num = util.number_format(second_prize_num[0]) if second_prize_num else 0
            third_prize = util.number_format(third_prize[0]) if third_prize else 0
            third_prize_num = util.number_format(third_prize_num[0]) if third_prize_num else 0
            fourth_prize = util.number_format(fourth_prize[0]) if fourth_prize else 0
            fourth_prize_num = util.number_format(fourth_prize_num[0]) if fourth_prize_num else 0
            fifth_prize = util.number_format(fifth_prize[0]) if fifth_prize else 0
            fifth_prize_num = util.number_format(fifth_prize_num[0]) if fifth_prize_num else 0
            sixth_prize = util.number_format(sixth_prize[0]) if sixth_prize else 0
            sixth_prize_num = util.number_format(sixth_prize_num[0]) if sixth_prize_num else 0
            seventh_prize = util.number_format(seventh_prize[0]) if seventh_prize else 0
            seventh_prize_num = util.number_format(seventh_prize_num[0]) if seventh_prize_num else 0
            open_result = {
                'first_prize': {'num': first_prize_num, 'amount': first_prize},
                'second_prize': {'num': second_prize_num, 'amount': second_prize},
                'third_prize': {'num': third_prize_num, 'amount': third_prize},
                'fourth_prize': {'num': fourth_prize_num, 'amount': fourth_prize},
                'fifth_prize': {'num': fifth_prize_num, 'amount': fifth_prize},
                'sixth_prize': {'num': sixth_prize_num, 'amount': sixth_prize},
                'seventh_prize': {'num': seventh_prize_num, 'amount': seventh_prize},
            }
            cp_id = util.cleartext(open_code, ',')
            cp_sn = int('11' + str(expect))
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'bet_amount': sales_count,
                'open_result': open_result,
                'create_time': util.date(),

            }
            # print('item', item)
            # print('db_name', db_name)
            # print('*' * 100)
            save_data(url, db_name, expect, item)

        # save_data(url, db_name, expect, item)


def save_data(url, db_name, expect, item):
    # print('item', item)
    # print('db_name', db_name)
    info = mysql.select(db_name, condition=[('expect', '=', expect)], limit=1)
    if not info:
        mysql.insert(db_name, data=item)
        _logger.info('INFO:数据保存成功, 期号%s ; URL:%s' % (expect, url))
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
    data = mysql.select('t_lottery',
                        fields=('abbreviation', 'lottery_name', 'lottery_type', 'lottery_result', 'jsh_open_url',
                                ))
    if not data:
        print('没有获取到数据')
        return
    proxy = get_prolist(20)

    CP = {
        89: 'https://www.jsh365.com/award/qg-his/fcsd.html',
        90: 'https://www.jsh365.com/award/qg-his/qlc.html',
        91: 'https://www.jsh365.com/award/qg-his/ssq.html',
        92: 'https://www.jsh365.com/award/qg-his/cjdlt.html',
        93: 'https://www.jsh365.com/award/qg-his/plw.html',
        94: 'https://www.jsh365.com/award/qg-his/pls.html',
        95: 'https://www.jsh365.com/award/qg-his/qxc.html',
    }
    RESULT = {
        89: 'game_sd_result',
        90: 'game_qlc_result',
        91: 'game_ssq_result',
        92: 'game_lotto_result',
        93: 'game_plw_result',
        94: 'game_pl3_result',
        95: 'game_qxc_result',
    }
    for key in CP:
        # if key != 95:
        #     continue

        url = CP[key].replace('.html', '/500.html')
        lottery_result = RESULT[key]
        # info = mysql.select(lottery_result,
        #                     fields=('open_time',), order='open_time desc', limit=1)
        # t = threading.Thread(target=run, args=(interval, info, proxy, _data, dlist), kwargs=kwargs,
        #                      name='thread-{0}'.format(len(task_list)))
        kwargs['url_type'] = key
        kwargs['db_name'] = lottery_result

        run(url, proxy, **kwargs)
        # break


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
