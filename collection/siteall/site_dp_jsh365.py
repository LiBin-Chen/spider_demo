#! /usr/bin/python
# -*- coding: utf-8 -*-

import time
import random
import logging
import requests
import argparse
import threading
from lxml import etree
from packages import Util as util, yzwl

__author__ = 'snow'
__time__ = '2019/3/7'

db = yzwl.DbClass()
mysql = db.yzwl
lock = threading.Lock()
_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

collection = db.mongo['pay_proxies']
default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}


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
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=proxies)
        # print('rs', rs.text)
        # exit()
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
    root = etree.HTML(data)
    # print('data',data)
    tr_list = root.xpath('//div[@class="container history"]//div[@class="tablebox ssqtable"]//table//tr')
    # print('tr_list', tr_list)
    # print('url', url)
    tr_list = reversed(tr_list)
    for tr in tr_list:
        item = {}
        text = tr.xpath('.//text()')
        text_list = []
        for _text in text:
            _text = util.cleartext(_text)
            if _text and _text != '详情':
                text_list.append(_text)
        # print('text_list', text_list)
        if not text_list or len(text_list) <= 3:
            _logger.info('INFO:数据不符合要求, data: %s ; URL:%s' % (text_list, url))
            continue
        item['expect'] = text_list[0]
        item['open_url'] = url
        item['create_time'] = util.date()
        item['open_time'] = text_list[1].split('(')[0]
        item['open_code'] = ','.join(text_list[2:])

        # print(item)
        # exit()
        info = mysql.select(db_name, condition={'expect': item['expect']}, limit=1)
        if info:
            _logger.info('INFO:数据已存在不做重复存入, 期号: %s ; URL:%s' % (item['expect'], url))
            continue
        mysql.insert(db_name, data=item)
        _logger.info('INFO:数据保存成功, 期号%s ; URL:%s' % (item['expect'], url))


def run(interval, info, proxy, _data, dlist, **kwargs):
    abbreviation = _data['abbreviation']
    lottery_name = _data['lottery_name']
    lottery_result = _data['lottery_result']
    lottery_chart_url = _data['lottery_chart_url']
    lottery_type = _data.get('lottery_type')
    if not lottery_chart_url:
        print('没有获取到有效链接')
        return
    open_time = info.get('open_time', '') if info else ''
    open_time = open_time.strftime('%Y-%m-%d') if open_time else None

    kwargs = {
        'db_name': lottery_result,
    }

    url = 'https://www.jsh365.com/award/dp-his/hljfcpne/500.html'
    url = lottery_chart_url.replace('dp-', 'dp-his/').replace('.html', '/500.html')
    result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)
    if not result:
        pass

    # if lottery_type == 'dp':
    #     url = 'https://www.jsh365.com/award/dp-his/hljfcpne/500.html'
    #     url = lottery_chart_url.replace('dp-', 'dp-his/').replace('.html', '/500.html')
    #     result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)
    #     if not result:
    #         pass
    # elif lottery_type == 'gp':
    #     for str_time in dlist:
    #         if open_time and str_time < open_time:
    #             '''
    #             若数据中存在的日期 则不再采集在此之前的数据
    #             '''
    #             _logger.info('INFO:数据已存在, 跳过该期数据:  {0};'.format(open_time))
    #             continue
    #         new_url = abbreviation + '/{0}'.format(str_time)
    #
    #         url = lottery_chart_url.replace(abbreviation, new_url)
    #         # print('url', url)
    #         # exit()
    #         result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)
    #         if not result:
    #             continue
    #         time.sleep(interval)
    # else:
    #     print('其他彩种')


def main(**kwargs):
    max_thread = 10
    task_list = []
    sd = kwargs.get('sd', '')
    ed = kwargs.get('sd', '')
    interval = kwargs.get('interval', 10)
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    data = mysql.select('t_lottery_jsh',
                        fields=('abbreviation', 'lottery_name', 'lottery_type', 'lottery_result', 'lottery_chart_url'))
    if not data:
        print('没有获取到数据')
        return
    proxy = get_prolist(20)
    dlist = util.specified_date(sd, ed)
    for _data in data:
        lottery_type = _data.get('lottery_type')
        if lottery_type != 'LOCAL':
            print('非低频数据 ...')
            continue
        kwargs['op_type'] = lottery_type
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
    while 1:
        cmd()
        print('-------------- sleep %s sec -------------' % 3600)
        time.sleep(3600)
