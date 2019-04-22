#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import logging
import requests
from config import LOTTO_RESULT
from packages import Util as util, yzwl

__author__ = 'snow'
'''程序

@description
    说明
'''

_logger = logging.getLogger('yzwl_spider')

default_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Cookie': 'UniqueID=KWpJJIaMMbeS4Oi01552741052640; Sites=_21; _ga=GA1.3.166127971.1552205553; _gid=GA1.3.1595082790.1552740249; _gat_gtag_UA_113065506_1=1; 21_vq=46',
    'Host': 'www.cwl.gov.cn',
    'Referer': 'http://www.cwl.gov.cn/kjxx/ssq/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}


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

    pass


def _parse_detail_data(data=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    pass


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
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


def api_fetch_data(url=None, **kwargs):
    '''
    从接口获取数据
    '''
    proxy = kwargs.get('proxy')
    url = kwargs.get('update_url')
    headers = kwargs.get('headers')

    # if isinstance(headers, dict):
    #     default_headers = headers
    try:
        proxies = kwargs.get('proxies')
        if proxies is None and proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {
                'http': 'http://' + proxy[1][i],
                'https': 'https://' + proxy[1][i]
            }
        res = requests.get(url=url, headers=default_headers, params=None, proxies=proxies)
        res.encoding = res.apparent_encoding

    except requests.RequestException as e:
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

    lotto_result_key = url.split('&')[0].split('name=')[-1]
    data_item = LOTTO_RESULT[lotto_result_key.upper()]

    try:
        data = res.json()
        result = data['result']
    except Exception as e:
        _logger.debug('STATUS:-404 ; INFO:数据异常  %s; URL:%s' % (e, url))
        return -404

    # http://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice?name=ssq&issueCount=1

    index_url = 'http://www.cwl.gov.cn'
    for info in result:
        expect = info['code']
        open_red_code = info['red']
        open_blue_code = info['blue']
        open_date = info['date']
        content = info['content']
        if not content and lotto_result_key != 'sd':
            return
        cp_id = open_red_code.replace(',', '') + open_blue_code
        cp_sn = '14' + str(expect)

        details_link = index_url + info['detailsLink']  # http://www.cwl.gov.cn/c/2019-03-14/450353.shtml
        video_link = index_url + info['videoLink']
        prizegrades = info['prizegrades']
        bonusSituationDtoList = data_item['bonusSituationDtoList']
        data_item['rolling'] = util.modify_unit(info['poolmoney'])
        data_item['nationalSales'] = util.modify_unit(info['sales'])

        bonusSituationDtoList[0]['numberOfWinners'] = prizegrades[0]['typenum']
        bonusSituationDtoList[0]['singleNoteBonus'] = prizegrades[0]['typemoney']

        bonusSituationDtoList[1]['numberOfWinners'] = prizegrades[1]['typenum']
        bonusSituationDtoList[1]['singleNoteBonus'] = prizegrades[1]['typemoney']

        bonusSituationDtoList[2]['numberOfWinners'] = prizegrades[2]['typenum']
        bonusSituationDtoList[2]['singleNoteBonus'] = prizegrades[2]['typemoney']

        open_time = open_date.split('(')[0] + ' 21:15:00'
        open_code = open_red_code + open_blue_code  # 3d

        if lotto_result_key in ['ssq', 'qlc']:
            open_code = open_red_code + '+' + open_blue_code  # ssq
            bonusSituationDtoList[3]['numberOfWinners'] = prizegrades[3]['typenum']
            bonusSituationDtoList[3]['singleNoteBonus'] = prizegrades[3]['typemoney']

            bonusSituationDtoList[4]['numberOfWinners'] = prizegrades[4]['typenum']
            bonusSituationDtoList[4]['singleNoteBonus'] = prizegrades[4]['typemoney']

            bonusSituationDtoList[5]['numberOfWinners'] = prizegrades[5]['typenum']
            bonusSituationDtoList[5]['singleNoteBonus'] = prizegrades[5]['typemoney']

            if lotto_result_key in ['qlc']:
                open_code = open_red_code + '+' + open_blue_code  # qlc
                bonusSituationDtoList[5]['numberOfWinners'] = prizegrades[6]['typenum']
                bonusSituationDtoList[5]['singleNoteBonus'] = prizegrades[6]['typemoney']
        count = 0
        for prize in bonusSituationDtoList:
            if lotto_result_key != 'sd':

                count += util.number_format(prize['numberOfWinners'], places=0) * util.number_format(
                    prize['singleNoteBonus'], places=0)
            else:
                count += util.number_format(
                    prize['singleNoteBonus'], places=0)

        data_item['currentAward'] = util.modify_unit(count)
        if lotto_result_key in ['ssq', 'qlc']:
            item = {
                # 'cp_id': cp_id,
                # 'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                'open_date': open_date,
                'open_url': '',
                'open_details_url': details_link,
                'details_link': details_link,
                'open_video_url': video_link,
                'open_content': content,
                'open_result': json.dumps(data_item, ensure_ascii=False),
                'create_time': util.date()
            }
        else:
            # 福彩3d，试机号从360彩票网站获取
            # test_code = get_3d_test_code(expect)
            item = {
                'cp_id': cp_id,
                'cp_sn': cp_sn,
                'expect': expect,
                'open_time': open_time,
                'open_code': open_code,
                # 'test_code': test_code,
                'open_date': open_date,
                'open_url': '',
                'open_details_url': details_link,
                'details_link': details_link,
                'open_video_url': video_link,
                'open_content': content,
                'open_result': json.dumps(data_item, ensure_ascii=False),
                'create_time': util.date()
            }
            # print('item', item)
    # print('item',item)
    return item


def fetch_update_data(url=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    # data = fetch_data(url, **kwargs)
    data = api_fetch_data(**kwargs)

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
    kwargs = {'id': 12, 'abbreviation': 'qlc', 'lottery_name': '七乐彩', 'lottery_type': 'NATIONWIDE',
              'update_url': 'http://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice?name=ssq&issueCount=1',
              'lottery_result': 'game_qlc_result',
              'headers': {'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20130331 Firefox/21.0'},
              'proxy': None}
    # fetch_data(url, **kwargs)
    fetch_update_data(**kwargs)
