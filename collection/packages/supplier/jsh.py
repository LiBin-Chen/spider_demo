#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'snow'
__time__ = '2019/3/11'

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
        # print('正在请求...', url)
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
    传入的数据有三种格式，分别是高频gp HIGH_RATE，地方dp  LOCAL ，全国qg NATIONWIDE，竞彩jc JC，由url可以作分析
    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    db_name = kwargs.get('db_name', '')
    lottery_type = kwargs.get('lottery_type', '')
    if not db_name:
        _logger.info('INFO: 请检查是否传入正确的数据库; URL:%s' % (url))
        return
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    # 在此 写解析语句/解析数据
    '''
    数据格式：
        期号
        开奖时间
        开奖号码
        开奖结果信息 json  包含中奖所有信息
        投注额度
        奖池
        中奖条件
        彩种开奖时间间隔(下期开奖时间)
        是否进行下次循环
    '''
    if lottery_type == 'HIGH_RATE':
        print('高频：', url)
        parse_xpath = {
            'root_xpath': '//table[@class="_tab"]//tr',  # table 列表
            'date_xpath': '//div[@class="_p2"]//text()',  # 高频开奖日期
            'latest_xpath': '//table[@class="_tab"]//tr//td[3]//text()',  # 最新一次开奖
            'expect_xpath': './/td[1]//text()',  # 期号
            'time_xpath': './/td[2]//text()',  # 开奖时间
            'code_xpath': './/td[3]//text()',  # 开奖结果
        }

        # root_xpath = '//table[@class="_tab"]//tr'

    elif lottery_type == 'LOCAL':
        print('地方：', url)
        parse_xpath = {
            'root_xpath': '//table[@class="_tab _tab2"]//tr',  # table 列表
            'date_xpath': '//span[@class="_time"]//text()',  # 低频开奖日期
            'latest_xpath': '//div[@class="_p2"]//div[@class="_balls"]//text()',  # 最新一次开奖
            'expect_xpath': './/td[1]//text()',  # 期号
            'time_xpath': './/td[3]//text()',  # 开奖时间
            'code_xpath': './/td[2]//text()',  # 开奖结果
        }
    elif lottery_type == 'NATIONWIDE':
        print('全国：', url)
        parse_xpath = {
            'root_xpath': '//table[@class="_tab _tab2"]//tr',  # table 列表
            'date_xpath': '//span[@class="_time"]//text()',  # 低频开奖日期
            'latest_xpath': '//div[@class="_p2"]//div[@class="_balls"]//text()',  # 最新一次开奖
            'expect_xpath': './/td[1]//text()',  # 期号
            'time_xpath': './/td[3]//text()',  # 开奖时间
            'code_xpath': './/td[2]//text()',  # 开奖结果
        }
        print('暂不在jsh更新全国性彩种')
        return
    elif lottery_type == 'JC':
        print('竞技彩：', url)
        return
    else:
        print('其他： ', url)

    # exit()

    root = etree.HTML(data)
    date_xpath = root.xpath(parse_xpath['date_xpath'])  # 判断日期是否是当天日期
    if not date_xpath:
        _logger.info('INFO: 该日期没有获取到数据; URL:%s' % (url))
    # print('date', date_xpath)
    today = str(int(util.number_format(util.cleartext(date_xpath[0], ':', '-', '年', '月', '日'))))  # 转成整数进行对比
    use_date = today[:4] + '-' + today[4:6] + '-' + today[6:] + ' '
    # print('today', today)
    print('use_date', use_date)
    tr_list = root.xpath(parse_xpath['root_xpath'])
    if not tr_list:
        _logger.info('INFO: 该日期没有获取到数据; URL:%s' % (url))
        return
    res = []
    for tr in tr_list:

        expect_xpath = tr.xpath(parse_xpath['expect_xpath'])
        time_xpath = tr.xpath(parse_xpath['time_xpath'])
        code_xpath = tr.xpath(parse_xpath['code_xpath'])
        if not expect_xpath:
            # _logger.info('INFO:该数据不符合要求 ; URL:%s' % (url))
            continue
        # print('expect_xpath', expect_xpath)
        # print('time_xpath', time_xpath)
        # print('code_xpath', code_xpath)

        '以中奖号+作为唯一id  各个网站+期号 作为 数据来源的标识 '

        code_list = []
        for _code in code_xpath:
            _code = util.cleartext(_code)
            if not _code:
                continue
            code_list.append(_code)
        expect = int(util.number_format(expect_xpath))
        open_code = ','.join(code_list)
        cp_code = ''.join(code_list)
        open_time = use_date + time_xpath[0] if ':' in time_xpath[0] else use_date
        create_time = util.date()
        cp_id = cp_code  # 以中奖号+作为唯一id 并且开奖时间间隔大于15分钟  高频彩最低为20分钟，连着开同号概率极小
        if lottery_type == 'NATIONWIDE':
            pass
        cp_sn = int(str(kwargs.get('wid', )) + str(expect)) if lottery_type != 'H' else int(
            str(kwargs.get('wid', )) + use_date.replace('-', '') + str(expect))
        item = {
            'cp_id': cp_id,
            'cp_sn': cp_sn,
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
            'create_time': create_time,
        }
        # print('item: ', item)
        # print('*' * 100)
        res.append(item)
    return res
    # info = mysql.select(db_name, condition={'expect': expect}, limit=1)
    # if info:
    #     _logger.info('INFO:数据已存在不做重复存入, 期号: %s ; URL:%s' % (expect, url))
    #     continue
    # mysql.insert(db_name, data=item)
    # _logger.info('INFO:数据保存成功, 期号%s ; URL:%s' % (expect, url))


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

    # print('_data', kwargs)
    # print('获取数据')
    data = fetch_data(url, **kwargs)
    '''
    在此进行数据存入
    '''
    # return data[0]
    # print('kw', kwargs)
    # print('最新一期。')
    if not data:
        return
    print('data', data[0])
    cp_id = data[0].get('cp_id')
    db_name = kwargs.get('db_name', '')
    if not db_name:
        return
    info = mysql.select(db_name, fields=('id', 'open_time',), condition={'cp_id': cp_id}, limit=1)
    # open_time = info.get('open_time', '')
    if not info:
        mysql.insert(db_name, data=data[0])
        _logger.info('INFO: 最新数据保存成功  期号：%s 开奖时间： %s; URL:%s' % (data[0]['expect'], data[0]['open_time'], url))
    else:
        mysql.update(db_name, condition={'id': info['id']}, data=data[0])
        _logger.info('INFO: 最新数据更新成功 ; URL:%s' % (url))
    # print('*' * 100)


def run(interval, info, proxy, _data, dlist, **kwargs):
    abbreviation = _data['abbreviation']
    lottery_name = _data['lottery_name']
    lottery_result = _data['lottery_result']
    lottery_chart_url = _data['lottery_chart_url']
    if not lottery_chart_url:
        print('没有获取到有效链接')
        return
    open_time = info.get('open_time', '') if info else ''
    open_time = open_time.strftime('%Y-%m-%d') if open_time else None

    kwargs = {
        'db_name': lottery_result,
    }
    for str_time in dlist:
        if open_time and str_time < open_time:
            '''
            若数据中存在的日期 则不再采集在此之前的数据
            '''
            _logger.info('INFO:数据已存在, 跳过该期数据:  {0};'.format(open_time))
            continue
        new_url = abbreviation + '/{0}'.format(str_time)
        url = lottery_chart_url.replace(abbreviation, new_url)
        result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)
        if not result:
            continue
        time.sleep(interval)


def main(**kwargs):
    max_thread = 10
    task_list = []
    sd = kwargs.get('sd', '')
    ed = kwargs.get('sd', '')
    interval = kwargs.get('interval', 10)
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    data = mysql.select('t_lottery',
                        fields=('abbreviation', 'lottery_name', 'lottery_type', 'lottery_result', 'lottery_chart_url'))
    if not data:
        print('没有获取到数据')
        return
    proxy = get_prolist(20)
    dlist = util.specified_date(sd, ed)
    for _data in data:
        lottery_type = _data.get('lottery_type')
        if lottery_type == 'dp':
            print('低频彩票数据网页结构不一样，跳过')
            continue
        lottery_result = _data.get('lottery_result')
        if lottery_result == 'game_nmgssc_result':
            continue
        info = mysql.select(lottery_result,
                            fields=('open_time',), order='open_time desc', limit=1)
        t = threading.Thread(target=run, args=(interval, info, proxy, _data, dlist), kwargs=kwargs,
                             name='thread-{0}'.format(len(task_list)))
        task_list.append(t)
        t.start()
        if len(task_list) >= max_thread:
            for t in task_list:
                t.join()
            task_list = []


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    # parser.add_argument('-u', '--url', help=u'从检索结果的 URL 开始遍历下载产品数据',
    #                     dest='url', action='store', default=None)
    parser.add_argument('-sd', '--sd', help=u'从指定日期开始下载数据',
                        dest='sd', action='store', default=None)
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

'''

输入/输出


'''
