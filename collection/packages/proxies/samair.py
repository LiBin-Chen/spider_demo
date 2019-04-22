#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging
from packages import Util

_logger = logging.getLogger('proxies')
#800多个代理IP,有效率百分之30多
__url__ = (
    'http://www.samair.ru/proxy/',
)


def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    data = fetch(url, **kwargs)
    if not data:
        _logger.info('STATUS:404 ; INFO:无数据 ; URL: %s' % url)
        return False
    subpage = kwargs.get('subpage',False)
    parse_only = SoupStrainer('div', id='content')
    bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
    if not bs.find('div', id='content'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False

    proxy_iplist = set()
    if 'ip-port' in url:
        proxy_data = bs.find('pre')
        if not proxy_data:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        proxy_list = proxy_data.get_text().split("\n")
        if not proxy_list:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            ip = Util.cleartext(proxy,' ')
            if not ip:
                continue
            proxy_iplist.add(ip)
        return proxy_iplist
    else:
        ipportonly = bs.find('div', id='ipportonly')
        if not ipportonly:
            return False
        try:
            ipport_url = 'http://www.samair.ru' + ipportonly.find('a')['href']
            res = fetch_proxy_data(ipport_url, subpage=True)
            res and proxy_iplist.update(res)
        except:
            _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False

    if not subpage:
        #获取分页数
        page_num = 1
        pages = bs.find_all('a', class_='page')
        if pages:
            page_num = int(pages[-2].get_text())

        print('正在获取分页数据，共有 %s 个分页...' % page_num)
        if page_num > 1:
            for i in range(2, page_num + 1):
                sub_url = '%sproxy-%02d.htm' % (url, i)
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res)

    return proxy_iplist