#! /usr/bin/python
# -*- coding: utf-8 -*-


import time
import re
import random
import logging
import requests
from lxml import etree
from packages import Util as util, yzwl

__author__ = 'snow'
__time__ = '2019/3/12'

'''
360彩票网封装函数    360

@description
    获取https://cp.360.cn/的彩票一级链接资料

'''
_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

top_url_compile = re.compile(r'type="text/javascript" src="(.*?)"')
sort_url_compile = re.compile(r"A href=\"(.*?)\" target=\"_blank\">(.*?)</A>", re.I)

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}

_header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
}
db = yzwl.DbClass()
mysql = db.yzwl

global_province = ''


def fetch_data(url_key, proxy=None, headers=None, **kwargs):
    '''
    获取页面数据
    @description
        获取数据彩数据

    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据


    '''
    cp = kwargs.get('cp')
    url = cp[url_key]
    if isinstance(headers, dict):
        default_headers = headers
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
        sess = requests.Session()
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

    return _parse_detail_data(rs.content, url_key, url=url, **kwargs)


def _parse_detail_data(data=None, url_key=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''

    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    root = etree.HTML(data)
    if root is None:
        return 0
    print('数据获取成功', root)

    if url_key == 5:
        tr_list = root.xpath('//div[@class="article"]//table//tr')
        prase_item = {
            'province': './/div[@class="abcdefg"]',  # 页面无省份，为全国 abcdefg设置取空,
            'lottery_name': './/h3/a/text()',
            'expect': './/td[2]//text()',
            'open_time': './/div[@class="abcdefg"]',  # 开奖时间
            'open_code': './/span[@class="kaij-data-list"]//em[@class="kaij-btn-boll"]//text()',  # 一级不用
            'lottery_detail_url': './/td//div[@class="kaij-data"]//span[last()]/a/@href',  # 彩种开奖详情
            'lottery_history_url': './/td//div[@class="tools"]//p//a[1]//@href',
            'lottery_zs_url': './/td//div[@class="tools"]//p//a[2]//@href',
            'lottery_news_url': './/td[8]/a/@href',
            'interval_time': './/span[@class="data"]//text()',
            'open_detail': '//td//div[@class="kaij-data"]//span[last()]/a/@href',  # 开奖详情
        }
    else:
        prase_item = None
    if prase_item is None:
        _logger.info('INFO:其他彩种or错误; %s ; URL :%s' % (url_key, url))
        exit()
    _logger.info('INFO:正在解析彩种类型; %s ; URL :%s' % (url_key, url))
    for tr in tr_list:
        province = tr.xpath(prase_item['province'])  # 彩种
        lottery_name = tr.xpath(prase_item['lottery_name'])  # 最新开奖链接
        expect = tr.xpath(prase_item['expect'])  # 期号
        open_time = tr.xpath(prase_item['open_time'])  # 开奖日期
        open_code = tr.xpath(prase_item['open_code'])  # 开奖结果
        lottery_detail_url = tr.xpath(prase_item['lottery_detail_url'])  # 详情链接
        lottery_history_url = tr.xpath(prase_item['lottery_history_url'])  # 历史链接
        lottery_zs_url = tr.xpath(prase_item['lottery_zs_url'])  # 走势链接
        lottery_news_url = tr.xpath(prase_item['lottery_news_url'])  # 资讯链接
        interval_time = tr.xpath(prase_item['interval_time'])  # 开奖日

        province = util.cleartext(province[0]) if province else '全国'
        global global_province
        if province == '全国' and url_key != 1:
            province = global_province
        global_province = province
        lottery_name = util.cleartext(lottery_name[0]) if lottery_name else ''
        expect = str(int((util.number_format(expect[0]) if expect else 0)))
        open_time = util.cleartext(open_time[0]) if open_time else ''
        lottery_detail_url = util.cleartext(lottery_detail_url[0]) if lottery_detail_url else ''
        lottery_history_url = util.cleartext(lottery_history_url[0]) if lottery_history_url else ''
        lottery_zs_url = util.cleartext(lottery_zs_url[0]) if lottery_zs_url else ''
        lottery_news_url = util.cleartext(lottery_news_url[0]) if lottery_news_url else ''
        interval_time = util.cleartext(interval_time[0]) if interval_time else ''
        open_time = expect[:4] + '-' + open_time.split('  ')[0]
        open_code_list = []
        for _code in open_code:
            _code = util.cleartext(_code)
            if _code:
                open_code_list.append(_code)
        open_code = ','.join(open_code_list)

        abbreviation = lottery_zs_url.split('?')[0].split('/')[-1]
        lottery_type = 'NATIONWIDE'

        lottery_result = 'sll_' + abbreviation + '_result' if url_key == 5 else 'sll_' + abbreviation + '_result'
        lottery_detail_url = 'https://cp.360.cn' + lottery_detail_url if 'http' not in lottery_detail_url else lottery_detail_url
        if not lottery_name:
            continue
        _item = {
            'province': province,
            'lottery_name': lottery_name,
            'abbreviation': abbreviation,
            'lottery_result': lottery_result,
            'lottery_type': lottery_type,
            'lottery_chart_url': lottery_detail_url,
            'lottery_history_url': lottery_history_url,
            'lottery_zs_url': lottery_zs_url,
            'lottery_news_url': lottery_news_url,
            'interval_time': interval_time,
        }

        print('_item', _item)
        # save_data(data=_item)


def save_data(href_name=None, href=None, time_list=None, data=None):
    '''
    保存数据

    :return:
    '''
    if data:
        info = mysql.select('t_lottery_sll', condition={'abbreviation': data['abbreviation']}, limit=1)
        if not info:
            mysql.insert('t_lottery_sll', data=data)
            print('新增成功')
        else:
            mysql.update('t_lottery_sll', condition={'id': info['id']}, data=data)
            print('修改成功')
    else:
        dlist = []
        for i in range(len(href_name)):
            if i % 4 == 0:
                item = {}
            item[href_name[i]] = href[i]
            if len(item) == 4:
                lottery_name = href_name[i - 3]
                lottery_chart_url = item[lottery_name]  # 开奖结果url
                lottery_url_abb = lottery_chart_url.split('/')[-1].split('.')[0]
                lottery_type = lottery_url_abb.split('-')[0]
                abbreviation = lottery_url_abb.split('-')[-1]
                lottery_result = 'game_' + abbreviation + '_result'
                lottery_zs_url = item['走势']
                new_item = {
                    'lottery_name': lottery_name,
                    'lottery_chart_url': lottery_chart_url,
                    'lottery_zs_url': lottery_zs_url,
                    'abbreviation': abbreviation,
                    'lottery_type': lottery_type,
                    'lottery_result': lottery_result,
                    'create_time': int(time.time()),
                    'update_time': int(time.time()),
                }
                dlist.append(new_item)
        for i in range(len(time_list)):
            dlist[i]['interval_time'] = time_list[i]

        for _item in dlist:
            # print('item', _item)
            info = mysql.select('t_lottery_sll', condition={'abbreviation': _item['abbreviation']}, limit=1)
            if not info:
                mysql.insert('t_lottery_sll', data=_item)
            else:
                mysql.update('t_lottery_sll', condition={'id': info['id']}, data=_item)


if __name__ == '__main__':
    CP = {
        1: 'https://www.jsh365.com/award.html',
        2: 'https://www.jsh365.com/award/gp.html',
        3: 'https://www.jsh365.com/award/dp.html',
        5: 'https://cp.360.cn/kj/kaijiang.html?src=topmenu&r_a=YJb6by'
    }
    kwargs = {
        'cp': CP,
    }
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    fetch_data(url_key=5, headers=_header, **kwargs)
