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

    return _parse_detail_data(rs.content, url=url, **kwargs)


def _parse_detail_data(**kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    pass


def save_data(url, db_name, item):
    info = mysql.select(db_name, condition=[('expect', '=', item['expect'])], limit=1)
    if not info:
        item['create_time']: util.date()
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ; URL:%s' % (db_name, item['expect'], url))

    else:
        item['update_time']: util.date()
        mysql.update(db_name, condition=[('expect', '=', item['expect'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在 更新成功, 期号: %s ; URL:%s' % (db_name, item['expect'], url))


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    '''
    根据关键词抓取搜索数据
    '''
    pass


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
        if res.status_code != 200:
            time.sleep(5)
            return
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
    if cp_genre == '9' and '+' in open_code:
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

    if cp_genre == '9':
        match_results = data_item['matchResults']
        matchResults = result[0]['matchResults']
        for i in range(len(matchResults)):
            match_results[i]['awayTeamView'] = util.cleartext(matchResults[i]['awayTeamView'], '<br>', '&nbsp;')
            match_results[i]['homeTeamView'] = util.cleartext(matchResults[i]['homeTeamView'], '<br>', '&nbsp;')
            match_results[i]['results'] = util.cleartext(matchResults[i]['results'])
        open_time = open_date.split(' ')[0].replace('年', '-').replace('月', '-').replace('日', '-') + ' 10:00:00'
        # 3代表主队胜1代表主客队平0代表主负

        # 更新一期时进行分数获取(新浪爱彩) 可能存在不同时更新的问题
        data_dict = fetch_update_data(expect)
        try:
            for i in range(len(matchResults)):
                match_results[i]['homeTeamView'] = data_dict[expect][i][0]
                match_results[i]['awayTeamView'] = data_dict[expect][i][1]
                match_results[i]['score'] = data_dict[expect][i][2]
        except:
            match_results[i]['score'] = '0:0'
    item = {
        'expect': expect,
        'open_time': open_time,
        'open_code': open_code,
        'open_date': open_date,
        'open_url': url,
        'open_details_url': '',
        'open_video_url': '',
        'open_content': '',
        'open_result': json.dumps(data_item, ensure_ascii=True),
        'source_sn': 17,

    }

    try:
        save_data(url, db_name, item)
    except Exception as e:
        _logger.exception('mysql异常： %s' % util.traceback_info(e))


def fetch_update_data(issue=None, id=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
    })
    r = session.get('https://kaijiang.aicai.com/sfc/')
    result_dict = {}
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        issues = selector.xpath('//*[@id="jq_last10_issue_no"]/option/text()')
        session.headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        url = 'https://kaijiang.aicai.com/open/historyIssue.do'
        post_data = {
            'gameIndex': 401,
            'issueNo': issue
        }
        r = session.post(url, post_data)
        if r.status_code == 200:
            data = json.loads(r.content.decode('utf8'))
            if data['raceHtml']:
                s = etree.HTML(data['raceHtml'])
                results = s.xpath('//tr')
                match_list = []
                for result in results:
                    host_team = result.xpath('./td[2]/i[1]/text()')[0]
                    score = result.xpath('./td[2]/i[2]/text()')[0]
                    away_team = result.xpath('./td[2]/i[3]/text()')[0]
                    match_list.append([host_team, away_team, score])
                result_dict[issue] = match_list
    return result_dict


def get_expect(lotto, num):
    '''
    获取期号
    :param lotto:
    :param num:
    :return:
    '''
    expect_url = 'http://www.lottery.gov.cn/historykj/history.jspx?_ltype={0}&page=false&termNum={1}&startTerm=&endTerm='.format(
        lotto, num)
    try:
        rs = requests.get(url=expect_url, headers=default_headers)
        rs.encoding = rs.apparent_encoding
        root = etree.HTML(rs.text)
        dlt_expect = root.xpath('//div[@class="result"]//tr//td[1]//text()')
    except Exception as e:
        _logger.info('INFO : 期号获取错误: {0}'.format(e))
        dlt_expect = []

    return dlt_expect


def main(**kwargs):
    past = kwargs.get('past', 5)
    cp_list = kwargs.get('cp', '4')
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
        '4': 'dlt',  # http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype=4&_term={0}
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

    while 1:
        # 采集 past 期的历史数据
        for _cp in cp_list:
            date_list = get_expect(CP[_cp], num=past)
            for expect in date_list:
                kwargs['db_name'] = RESULT[_cp]
                kwargs['genre'] = _cp
                url = 'http://www.lottery.gov.cn/api/lottery_kj_detail_new.jspx?_ltype={0}&_term={1}'.format(_cp,
                                                                                                             expect)
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
    parser.add_argument('-p', '--past', help=u'下载历史数据 数量 默认过去5期',
                        dest='past', action='store', default=5)
    parser.add_argument('-C', '--cp', help='指定更新彩种(可多选)，不选默认为所有彩种',
                        nargs='+')
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
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
