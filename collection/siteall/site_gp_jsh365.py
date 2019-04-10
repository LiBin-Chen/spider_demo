#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import random
import logging
import requests
import argparse
import datetime
import threading
from lxml import etree

try:
    from packages import yzwl
    from packages import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.yzwl as yzwl
    import packages.Util as util

__author__ = 'snow'
__time__ = '2019/3/2'
'''
极速虎网封装函数    jsh365

@description
    收集更新彩票数据

'''

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

# collection = db.mongo['pay_proxies']
default_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.jsh365.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.yzwl
test_mysql = db.test_yzwl
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

    if isinstance(headers, dict):
        default_headers = headers
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}

        # sess = requests.Session()
        # _logger.info('INFO:使用代理, %s ;' % (proxies))
        rs = requests.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=proxies)
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
    lottery_type = kwargs.get('lottery_type', '')
    if not db_name:
        _logger.info('INFO: 请检查是否传入正确的数据库; URL:%s' % url)
        return
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
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
        return
    elif lottery_type == 'JC':
        print('竞技彩：', url)
        return
    else:
        print('其他： ', url)
        return

    root = etree.HTML(data)
    date_xpath = root.xpath(parse_xpath['date_xpath'])  # 判断日期是否是当天日期
    if not date_xpath:
        _logger.info('INFO: 该日期没有获取到数据; URL:%s' % (url))

    today = str(int(util.number_format(util.cleartext(date_xpath[0], ':', '-', '年', '月', '日'))))  # 转成整数进行对比
    use_date = today[:4] + '-' + today[4:6] + '-' + today[6:] + ' '
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
            # print('无效数据...')
            continue

        '以中奖号+作为唯一id  各个网站+期号 作为 数据来源的标识 '

        code_list = []
        for _code in code_xpath:
            _code = util.cleartext(_code)
            if not _code:
                continue
            code_list.append(_code)
        # print('expect_xpath', expect_xpath)
        # expect = util.number_format(expect_xpath)
        # expect = str(expect).split('.')[0]
        expect = util.cleartext(use_date, '-') + expect_xpath[1] if lottery_type == 'HIGH_RATE' else util.cleartext(
            expect_xpath[0], '期')
        open_code = ','.join(code_list)
        cp_code = ''.join(code_list)
        if lottery_type == 'HIGH_RATE':
            open_time = use_date + time_xpath[0] if ':' in time_xpath[0] else use_date
        else:
            open_time = expect[:4] + '-' + time_xpath[0]
        create_time = util.date()
        cp_id = cp_code  # 以中奖号+作为唯一id 并且开奖时间间隔大于15分钟  高频彩最低为20分钟，连着开同号概率极小
        cp_sn = int(str(11) + str(expect))
        item = {
            'cp_id': cp_id,
            'cp_sn': cp_sn,
            'expect': expect,
            'open_time': open_time,
            'open_code': open_code,
            'open_url': url,
            'create_time': create_time,
        }
        # print('item', item)
        # print('*' * 100)
        info = mysql.select(db_name, condition=[('cp_id', '=', cp_id), ('cp_sn', '=', cp_sn)], limit=1)
        if not info:
            mysql.insert(db_name, data=item)
            test_mysql.insert(db_name, data=item)
            _logger.info('INFO: 数据库： %s 数据保存成功, 期号 %s ; URL:%s' % (db_name, expect, url))
        else:
            mysql.update(db_name, condition={'id': info['id']}, data=item)
            _logger.info('INFO: 数据库： %s 数据更新成功, 期号 %s ; URL:%s' % (db_name, expect, url))


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
        print('proxies', proxies)
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


def main(**kwargs):
    task_list = []
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    past = kwargs.get('past', '')
    interval = kwargs.get('interval', 10)
    _headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'www.jsh365.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
    }
    data = mysql.select('t_lottery',
                        fields=(
                            'abbreviation', 'key_python', 'lottery_name', 'lottery_type', 'lottery_result',
                            'jsh_open_url'))
    if not data:
        print('没有获取到数据')
        return

    proxy = get_prolist(20)
    dlist = util.specified_date(sd, ed)

    for _data in data:
        lottery_type = _data.get('lottery_type')
        lottery_result = _data.get('lottery_result')
        jsh_open_url = _data.get('jsh_open_url')
        abbreviation = _data['key_python']
        lottery_name = _data['lottery_name']
        if lottery_result in ['game_pk10_result', 'game_cqssc_result', 'game_tjssc_result', 'game_jsks_result',
                              'game_xjssc_result', 'game_gdklsf_result']:
            continue
        kwargs = {
            'db_name': lottery_result,
            'lottery_type': lottery_type,
        }
        if not jsh_open_url:
            print('没有获取到有效链接')
            continue
        if lottery_name in ['NATIONWIDE']:  # 不采集全国性彩种
            continue
        if not lottery_result or lottery_result in ['game_nmgssc_result']:  # 该网站不做更新的彩种
            continue

        if not past:
            '获取最新一天的数据'
            result = fetch_data(url=jsh_open_url, proxy=proxy, headers=default_headers, **kwargs)

        else:
            info = mysql.select(lottery_result,
                                fields=('open_time',), order='open_time desc', limit=1)
            url = jsh_open_url
            if lottery_type != 'HIGH_RATE':
                'https://www.jsh365.com/award/qg-cjdlt.html'
                'https://www.jsh365.com/award/qg-his/cjdlt/500.html'
                'https://www.jsh365.com/award/dp-gdnyfcsnxq.html'
                'https://www.jsh365.com/award/dp-his/gdnyfcsnxq/500.html'
                # 以最新开奖链接组装成历史的链接
                temp_url_list = jsh_open_url.split('-')
                url = temp_url_list[0] + '-his/' + temp_url_list[-1].split('.')[0] + '/500.html'

            open_time = info.get('open_time', '') if info else ''
            open_time = open_time.strftime('%Y-%m-%d') if open_time else None
            for str_time in dlist:
                new_url = abbreviation + '/{0}'.format(str_time)
                url = url.replace(abbreviation, new_url)
                result = fetch_data(url=jsh_open_url, proxy=proxy, headers=default_headers, **kwargs)


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    # parser.add_argument('-u', '--url', help=u'从检索结果的 URL 开始遍历下载产品数据',
    #                     dest='url', action='store', default=None)
    parser.add_argument('-p', '--past', help=u'默认最新一期数据',
                        dest='past', action='store', default=0)
    parser.add_argument('-sd', '--sd', help=u'从指定日期开始下载数据',
                        dest='sd', action='store', default='03/17/2019')
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

    while 1:
        hour = datetime.datetime.today().hour
        if hour <= 8:
            print('暂停中...')
            continue
        else:
            cmd()
        time.sleep(1800)
