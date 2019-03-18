# ! /usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys
import time
import json
import random
import logging
import requests
import argparse
import threading
from lxml import etree

try:
    from packages import yzwl
    from packages import Util as util
    from siteall.check_list import get_gov_expexc
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.yzwl as yzwl
    import packages.Util as util
    from siteall.check_list import get_gov_expexc

__author__ = 'snow'
__time__ = '2019/3/17'

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

default_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'Hm_lvt_8929ffae85e1c07a7ded061329fbf441=1552747216,1552766134,1552795581,1552801656; Hm_lpvt_8929ffae85e1c07a7ded061329fbf441=1552801656; JSESSIONID=DD2F72D3F13026DECABD380A61FC5887',
    'Host': 'www.lottery.gov.cn',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.local_yzwl
lock = threading.Lock()


def get_prolist(limit):
    '''
    获取代理列表
    直接从数据库获取，可改为接口获取
    :param limit:
    :return:
    '''
    count = mysql.count('proxies') - limit
    end_number = random.randint(1, count)
    condition = [('pid', '>=', end_number), ('is_pay', '=', 1), ('is_use', '=', 1)]
    data = mysql.select('proxies', condition=condition, limit=limit)
    if isinstance(data, dict):
        return [1, {'ip': data['ip']}]
    dlist = []
    for _data in data:
        # item = {
        #     'ip': _data['ip'],
        # }
        dlist.append(_data['ip'])
    _num = len(dlist)
    return [_num, dlist]


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

    # if isinstance(headers, dict):
    #     default_headers = headers
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}

        sess = requests.Session()
        _logger.info('INFO:使用代理, %s ;' % (proxies))

        print('获取url： {0}'.format(url))
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=None)
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
    # rs.encoding = 'utf-8'
    rs.encoding = rs.apparent_encoding
    with lock:
        return _parse_detail_data(rs.content, url=url, **kwargs)


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
    root = etree.HTML(data)


def save_data(url, db_name, item, sign=None):
    info = mysql.select(db_name, condition=[('expect', '=', item['expect'])], limit=1)
    if not info:
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ; URL:%s' % (db_name, item['expect'], url))
        if sign:
            sys.exit()
    else:
        mysql.update(db_name, condition=[('expect', '=', item['expect'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在 更新成功, 期号: %s ; URL:%s' % (db_name, item['expect'], url))


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


def api_fetch_data(url=None, proxy=None, **kwargs):
    '''
    从接口获取数据
    '''
    db_name = kwargs.get('db_name', '')
    if not db_name:
        return
    proxies = kwargs.get('proxies')
    if proxies is None and proxy:
        i = random.randint(0, proxy[0] - 1)
        proxies = {
            'http': 'http://' + proxy[1][i],
            'https': 'https://' + proxy[1][i]
        }

    if not url:
        return None
    parm_data = {
    }
    try:
        proxies = None
        if isinstance(url, tuple):
            url = url[0]
        res = requests.get(url=url, headers=default_headers, params=parm_data, proxies=proxies)
        res.encoding = res.apparent_encoding
    except requests.RequestException as e:
        print('从接口获取数据失败')
        return -1
    result = res.json()

    cp_genre = kwargs.get('genre')
    if cp_genre is '4':
        data_item = {"rolling": "0", "nationalSales": "0", "currentAward": "0", "bonusSituationDtoList": [
            {"numberOfWinners": "0", "singleNoteBonus": "0", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "5+2", "prize": "一等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "0", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "5+1", "prize": "二等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "10000", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "5+0", "prize": "三等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "3000", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "4+2", "prize": "四等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "300", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "4+1", "prize": "五等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "200", "winningConditions": "3+2",
             "prize": "六等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "100", "winningConditions": "4+0", "prize": "七等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "15", "winningConditions": "3+1,2+2",
             "prize": "八等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "5", "winningConditions": "3+0,1+2,2+1,0+2",
             "prize": "九等奖"},
        ]}
    elif cp_genre == '5':
        data_item = {
            "rolling": "0",
            "bonusSituationDtoList": [
                {
                    "winningConditions": "号码按位相符",
                    "numberOfWinners": "0",
                    "singleNoteBonus": "1,040",
                    "prize": "直选"
                },
                {
                    "winningConditions": "号码按位相符",
                    "numberOfWinners": "0",
                    "singleNoteBonus": "346",
                    "prize": "组选3"
                },
                {
                    "winningConditions": "号码相符(无同号)",
                    "numberOfWinners": "0",
                    "singleNoteBonus": "173",
                    "prize": "组选6"
                }
            ],
            "nationalSales": "0",
            "currentAward": "0"
        }
    elif cp_genre == '6':
        data_item = {
            "rolling": "0",
            "bonusSituationDtoList": [
                {
                    "winningConditions": "号码按位相符",
                    "numberOfWinners": "0",
                    "singleNoteBonus": "0",
                    "prize": "直选"
                },
            ],
            "nationalSales": "0",
            "currentAward": "0"
        }
    elif cp_genre == '8':
        data_item = {"rolling": "0", "bonusSituationDtoList": [
            {"winningConditions": "定位中7码", "numberOfWinners": "0", "singleNoteBonus": "0",
             "prize": "\u4e00\u7b49\u5956"},
            {"winningConditions": "定位中连续6码", "numberOfWinners": "0", "singleNoteBonus": "0",
             "prize": "\u4e8c\u7b49\u5956"},
            {"winningConditions": "定位中连续5码", "numberOfWinners": "0", "singleNoteBonus": "1800",
             "prize": "\u4e09\u7b49\u5956"},
            {"winningConditions": "定位中连续4码", "numberOfWinners": "0", "singleNoteBonus": "300",
             "prize": "\u56db\u7b49\u5956"},
            {"winningConditions": "定位中连续3码", "numberOfWinners": "0", "singleNoteBonus": "20",
             "prize": "\u4e94\u7b49\u5956"},
            {"winningConditions": "定位中连续2码", "numberOfWinners": "0", "singleNoteBonus": "5",
             "prize": "\u516d\u7b49\u5956"}], "nationalSales": "13652.343\u4e07", "currentAward": "15620.114\u4e07"}
    elif cp_genre == '9':
        data_item = {"rolling": "0", "nationalSales": "0", "currentAward": "0", "bonusSituationDtoList": [
            {"numberOfWinners": "0", "singleNoteBonus": "0", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "14场比赛的胜平负结果全中", "prize": "一等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "0", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "13场比赛的胜平负结果全中", "prize": "二等奖"},
            {"numberOfWinners": "0", "singleNoteBonus": "10000", "additionNumber": "0",
             "additionBonus": "0", "winningConditions": "14场选9场比赛胜平负结果全中", "prize": "任9"},

        ],
                     'matchResults': [
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                         {"awayTeamView": "0", "homeTeamView": "0", "results": "0", "score": "--"},
                     ],
                     }
    else:
        pass
    try:
        lottery = result[0]['lottery']
    except:
        _logger.info('INFO:  数据获取错误 ; URL:%s' % (url))
        return
    if cp_genre is '4':
        details = result[0]['details']
        detailsAdd = result[0]['detailsAdd']
    else:
        details = result[0]['details']

    open_code = lottery['number'].replace(' ', ',').replace('-', '+')
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
        if cp_genre is '4':
            bonusSituationDtoList[i]['additionNumber'] = util.number_format(util.cleartext(detailsAdd[i]['piece'], ','),
                                                                            places=0)
            bonusSituationDtoList[i]['additionBonus'] = util.number_format(util.cleartext(detailsAdd[i]['money'], ','),
                                                                           places=0)
            count += util.number_format(util.cleartext(details[i]['allmoney']), places=0) + util.number_format(
                util.cleartext(detailsAdd[i]['allmoney']), places=0)
        else:
            count += util.number_format(util.cleartext(details[i]['allmoney']), places=0)

    data_item['currentAward'] = util.modify_unit(count)
    cp_id = open_code.replace(',', '').replace('+', '')
    cp_sn = '17' + str(expect)

    if cp_genre == '9':
        match_results = data_item['matchResults']
        matchResults = result[0]['matchResults']
        for i in range(len(matchResults)):
            match_results[i]['awayTeamView'] = util.cleartext(matchResults[i]['awayTeamView'], '<br>', '&nbsp;')
            match_results[i]['homeTeamView'] = util.cleartext(matchResults[i]['homeTeamView'], '<br>', '&nbsp;')
            match_results[i]['results'] = util.cleartext(matchResults[i]['results'])
        open_time = open_date.split(' ')[0].replace('年', '-').replace('月', '-').replace('日', '-') + ' 10:00:00'
        # 3代表主队胜1代表主客队平0代表主负
    item = {
        'cp_id': cp_id,
        'cp_sn': cp_sn,
        'expect': expect,
        'open_time': open_time,
        'open_code': open_code,
        'open_date': open_date,
        'open_url': url,
        'open_details_url': '',
        'open_video_url': '',
        'open_content': '',
        'open_result': json.dumps(data_item, ensure_ascii=True),
        'create_time': util.date()
    }
    # print('*' * 100)
    # print('item', item)
    # try:
    #     sign = kwargs.get('sign', '')
    #     save_data(url, db_name, item, sign)
    # except Exception as e:
    #     _logger.exception('mysql异常： %s' % util.traceback_info(e))
    # return result


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


def main(**kwargs):
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    cp_list = kwargs.get('cp', '1')
    task_list = []
    past = kwargs.get('past', 0)
    sign = kwargs.get('sign', 0)
    interval = kwargs.get('interval', 10)
    _header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': 'Hm_lvt_8929ffae85e1c07a7ded061329fbf441=1552747216,1552766134,1552795581,1552801656; Hm_lpvt_8929ffae85e1c07a7ded061329fbf441=1552801656; JSESSIONID=DD2F72D3F13026DECABD380A61FC5887',
        'Host': 'www.lottery.gov.cn',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    proxy = util.get_prolist(10)
    CP = {
        '4': 'lotto',  # http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=4&_term={0}
        '5': 'pls',  # http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=5&_term=
        '6': 'plw',  # http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=8&_term=
        '8': 'qxc',  # http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=8&_term=
        '9': 'sfc',  # http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=8&_term=
    }
    'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=5&_term='  # 排列3 和排列5
    RESULT = {
        '4': 'game_lotto_result',
        '5': 'game_pl3_result',
        '6': 'game_plw_result',
        '8': 'game_qxc_result',
        '9': 'game_sfc_result',
    }
    FILE_DICT = {
        '4': r'E:\pySpace\yzwl\collection\packages\siteall\lotto.txt',
        '5': r'E:\pySpace\yzwl\collection\packages\siteall\pls.txt',
        '6': r'E:\pySpace\yzwl\collection\packages\siteall\plw.txt',
        '8': r'E:\pySpace\yzwl\collection\packages\siteall\qxc.txt',
        '9': r'E:\pySpace\yzwl\collection\packages\siteall\sfc.txt',
    }

    while 1:
        if past:
            # 下载所有的历史数据
            for _cp in cp_list:
                dlist = get_gov_expexc(FILE_DICT[_cp], f=True)
                for expect in dlist:
                    kwargs['db_name'] = RESULT[_cp]
                    kwargs['genre'] = _cp
                    url = 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype={0}&_term={1}'.format(_cp,
                                                                                                                 expect)
                    print('正在请求url: ', url)
                    api_fetch_data(url, proxy=proxy, **kwargs)
        else:
            # 获取最新一期的数据
            newest_CP = {
                '4': 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=4&_term=',
                '5': 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=5&_term=',
                '6': 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=6&_term=',
                '8': 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=8&_term=',
                '9': 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=9&_term=',
            }
            for _cp in cp_list:
                kwargs['db_name'] = RESULT[_cp]
                kwargs['genre'] = _cp
                url = newest_CP[_cp]
                kwargs['sign'] = sign
                print('正在请求url: ', url)
                api_fetch_data(url, proxy=proxy, **kwargs)

        if not interval:
            break
        print('-------------- sleep %s sec -------------' % interval)
        time.sleep(interval)


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-p', '--past', help=u'下载历史数据',
                        dest='past', action='store', default=1)
    parser.add_argument('-s', '--sign', help=u'定时任务时使用获取到开奖结果即关闭程序的标记',
                        dest='sign', action='store', default=0)
    parser.add_argument('-sd', '--sd', help=u'指定开始下载日期',
                        dest='sd', action='store', default='2010-10-23')
    parser.add_argument('-ed', '--ed', help=u'指定结束下载日期',
                        dest='ed', action='store', default='2019-03-17')
    parser.add_argument('-C', '--cp', help='指定更新彩种(可多选)，不选默认为所有彩种',
                        nargs='+')
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    args.cp = ['9']
    if not args.cp:
        args.cp = ['4', '5', '6', '8', '9']
    if args.help:
        parser.print_help()
        print(u"\n示例")

    elif args.past or args.sd:
        # args.cp = ['2', ]
        main(**args.__dict__)
    else:
        main()


if __name__ == '__main__':
    cmd()
