#! /usr/bin/python
# -*- coding: utf-8 -*-


__author__ = 'snow'
__time__ = '2019/4/16'

import time
import json
import random
import logging
import requests
import argparse
import threading
from lxml import etree
from packages import Util as util, yzwl

'''

@description
    收集espn球队信息

'''

_logger = logging.getLogger('yzwl_spider')

# _cookies = {'MAINT_NOTIFY_201410': 'notified'}

db = yzwl.DbSession()
collection = db.mongo['pay_proxies']
default_headers = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
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
        print('获取url： {0}'.format(url))
        rs = sess.get(url, headers=default_headers, cookies=None, timeout=30, proxies=None)

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
    # util.save_html(rs.text,'nba.html')
    # text = util.fetch_html('Z:\spider\yzwl\collection\html\nba.html')
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
    # root=etree.htmlfile(data)
    root = etree.HTML(data)
    # team_division = root.xpath('//div[@class="layout is-split"]//div[@class="mt7"]/div/text()')
    # print('team_division', team_division)   #nba赛区

    teams = root.xpath('//div[@class="layout is-split"]//div[@class="mt7"]//div[@class="mt3"]')
    index_url = 'http://www.espn.com'
    for team in teams:
        try:
            team_name_en = team.xpath('.//div[@class="pl3"]/a/h2/text()')[0]
            team_link_span = team.xpath('.//div[@class="TeamLinks__Links"]//span')
            team_stats_url = index_url + team_link_span[0].xpath('./a/@href')[0]
            team_schedule_url = index_url + team_link_span[1].xpath('./a/@href')[0]
            team_roster_url = index_url + team_link_span[2].xpath('./a/@href')[0]
            team_depth_url = index_url + team_link_span[3].xpath('./a/@href')[0]
        except Exception as e:
            # team_name = ''
            # team_stats_url = ''
            # team_schedule_url = ''
            # team_roster_url = ''
            # team_depth_url = ''
            _logger.debug('STATUS: 0001 ; INFO: 数据解析错误', util.traceback_info(e))
            continue

        # print('team_name_en', team_name_en)
        # print('team_stats_url', team_stats_url)
        # print('team_schedule_url', team_schedule_url)
        # print('team_roster_url', team_roster_url)
        # print('team_depth_url', team_depth_url)
        #
        # print('*' * 200)

        item = {
            'team_name_en': team_name_en,
            'team_stats_url': team_stats_url,
            'team_schedule_url': team_schedule_url,
            'team_roster_url': team_roster_url,
            'team_depth_url': team_depth_url,
            'update_time_stamp': int(time.time())
        }
        save_data(url, db_name='t_basketball_team', item=item)
        # exit()


def parse_data(data, symol=1):
    data_list = []

    for _data in data:
        if symol == 1:
            _data = util.cleartext(_data)
        else:
            _data = int(util.number_format(util.cleartext(_data)))
        data_list.append(_data)

    return data_list


def save_data(url, db_name, item):
    team_name_en = item['team_name_en']
    team_short_name_en = ' '.join(team_name_en.split(' ')[1:])
    fields = ('team_id', 'team_name_zh', 'create_time', 'update_time')
    info = mysql.select(db_name, fields=fields, condition=[('team_short_name_en', '=', team_short_name_en)], limit=1)
    print('info', info)
    if not info:
        data = mysql.select(db_name, fields=('team_id'), order='team_id DESC', limit=1)
        team_id = data['team_id'] + 1
        item['team_id'] = team_id
        # mysql.insert(db_name, data=item, return_insert_id=True)
        _logger.info('INFO:数据新增 保存操作, 球队ID: {0} ; 球队名称: {1}'.format(team_id, team_name_en))
    else:
        mysql.update(db_name, condition=[('team_id', '=', info['team_id'])], data=item)
        _logger.info('INFO:数据已存在 更新操作, 球队ID: {0} ; 球队名称: {1}'.format(info['team_id'], info['team_name_zh']))


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
        rs = requests.get(url, headers=default_headers, cookies=None, timeout=20, proxies=proxies)
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


def main(**kwargs):
    max_thread = 10
    task_list = []
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    interval = kwargs.get('interval', 10)
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }

    # proxy = get_prolist(20)

    url = 'http://www.espn.com/nba/teams'

    fetch_data(url, proxy=None, headers=None, **kwargs)


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
    # cmd()
    url = 'http://www.espn.com/nba/teams'
    text = util.fetch_html(file_name='nba.html')
    # print('text',text)
    _parse_detail_data(text, url)
'''
//div[@class="TeamLinks__Links"]//span[1]/a/@href   stats
//div[@class="TeamLinks__Links"]//span[2]/a/@href   schedule
//div[@class="TeamLinks__Links"]//span[3]/a/@href   roster
//div[@class="TeamLinks__Links"]//span[4]/a/@href  depth
'''
