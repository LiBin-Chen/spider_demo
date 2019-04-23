#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
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
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
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


def api_fetch_data(url=None, **kwargs):
    '''
    从接口获取数据
    '''

    url = kwargs.get('update_url')
    lotto_result_key = int(url.split('&')[0].split('=')[-1])
    headers = kwargs.get('headers')
    if isinstance(headers, dict):
        default_headers = headers
    try:
        proxy = 0
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
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

    data_item = LOTTO_RESULT[lotto_result_key]

    try:
        result = res.json()
        lottery = result[0]['lottery']
    except Exception as e:
        _logger.debug('STATUS:-404 ; INFO:数据异常  %s; URL:%s' % (e, url))
        return -404
    if lotto_result_key == 4:
        details = result[0]['details']
        detailsAdd = result[0]['detailsAdd']
    else:
        details = result[0]['details']

    open_code = lottery['number'].replace(' ', ',').replace('-', '+')
    if lotto_result_key == 9 and '+' in open_code:  # 这个为胜负彩的彩种
        sys.exit()
    expect = lottery['term']
    open_time = lottery['fTime'].split(' ')[0] + ' 20:30:00'
    open_date = lottery['openTime_fmt']
    data_item['nationalSales'] = util.modify_unit(lottery['totalSales'])
    data_item['rolling'] = util.modify_unit(lottery['pool'])
    bonusSituationDtoList = data_item['bonusSituationDtoList']
    count = 0
    for i in range(len(details)):
        bonusSituationDtoList[i]['numberOfWinners'] = util.number_format(util.cleartext(details[i]['piece'], ','),
                                                                         places=0)
        bonusSituationDtoList[i]['singleNoteBonus'] = util.number_format(util.cleartext(details[i]['money'], ','),
                                                                         places=0)
        if lotto_result_key == 4:
            bonusSituationDtoList[i]['additionNumber'] = util.number_format(util.cleartext(detailsAdd[i]['piece'], ','),
                                                                            places=0)
            bonusSituationDtoList[i]['additionBonus'] = util.number_format(util.cleartext(detailsAdd[i]['money'], ','),
                                                                           places=0)
            count += util.number_format(util.cleartext(details[i]['allmoney']), places=0) + util.number_format(
                util.cleartext(detailsAdd[i]['allmoney']), places=0)
        else:
            count += util.number_format(util.cleartext(details[i]['allmoney']), places=0)

    data_item['currentAward'] = util.modify_unit(count)

    if lotto_result_key == 9:
        match_results = data_item['matchResults']
        matchResults = result[0]['matchResults']
        for i in range(len(matchResults)):
            match_results[i]['awayTeamView'] = util.cleartext(matchResults[i]['awayTeamView'], '<br>', '&nbsp;')
            match_results[i]['homeTeamView'] = util.cleartext(matchResults[i]['homeTeamView'], '<br>', '&nbsp;')
            match_results[i]['results'] = util.cleartext(matchResults[i]['results'])
        open_time = open_date.split(' ')[0].replace('年', '-').replace('月', '-').replace('日', '-') + ' 10:00:00'
        # 3代表主队胜1代表主客队平0代表主负
        # if sign:
        #     # 更新一期时进行分数获取(新浪爱彩) 可能存在不同时更新的问题
        #     data_dict = fetch_update_data(expect)
        #     try:
        #         for i in range(len(matchResults)):
        #             match_results[i]['homeTeamView'] = data_dict[expect][i][0]
        #             match_results[i]['awayTeamView'] = data_dict[expect][i][1]
        #             match_results[i]['score'] = data_dict[expect][i][2]
        #     except:
        #         match_results[i]['score'] = '0:0'
    item = {
        'expect': expect,
        'open_time': open_time,
        'open_code': open_code,
        'open_date': open_date,
        'open_url': url,
        'open_details_url': '',
        'open_video_url': '',
        'open_content': '',
        'open_result': json.dumps(data_item, ensure_ascii=False),
        'source_sn': 17,
        'create_time': util.date()
    }
    # print('item', item)
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
    kwargs = {'id': 51, 'abbreviation': 'rx9', 'lottery_name': '任选9', 'lottery_type': 'SPORTS',
              'update_url': 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=9&_term=',
              'lottery_result': 'game_sfc_result', 'headers': {
            'user-agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; InfoPath.2; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'},
              'proxy': None, 'status': -400, 'count': 1}
    fetch_update_data(**kwargs)
