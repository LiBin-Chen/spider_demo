#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging
from packages import Util as util

_logger = logging.getLogger('proxies')

'''
didsoft免费代理IP，每天更新
'''
__url__ = (
    # 'http://www.google-proxy.net/',
    'http://free-proxy-list.net/',
    'http://www.us-proxy.org/',
    'http://free-proxy-list.net/anonymous-proxy.html',
    # 'http://www.freeproxylists.net/zh',
    # 'http://www.socks-proxy.net/',
    'http://incloak.com/proxy-list/?type=h',
    'http://www.proxylisty.com/ip-proxylist',
)


def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    kw = kwargs.copy()
    # fix: 临时处理，上面站点被墙
    # kw['proxies'] = {
    #     'http': 'http://43.245.220.11:8080',
    # }
    data = fetch(url, **kw)
    if not data:
        return False
    is_not = False
    if 'incloak.com' in url:
        parse_only = SoupStrainer('table', class_='proxy__t')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table', class_='proxy__t'):
            is_not = True
    elif 'proxylisty.com' in url:
        parse_only = SoupStrainer('table')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table'):
            is_not = True
    else:
        parse_only = SoupStrainer('table', id='proxylisttable')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table', id='proxylisttable'):
            is_not = True
    if is_not:
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    try:
        proxy_list = bs.find('tbody').find_all('tr')
    except:
        _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)
        return False
    if not proxy_list:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False
    proxy_iplist = set()
    for proxy in proxy_list:
        try:
            proxy = proxy.find_all('td')
            if 'proxylisty.com' in url:
                _type = util.cleartext(proxy[2].text).lower()
            else:
                _type = util.cleartext(proxy[4].text).lower()
            if _type in ('socks4', 'socks5'):
                continue
            port = util.number_format(proxy[1].text, 0)
            if port <= 0:
                continue
            ip = '%s:%s' % (proxy[0].text, port)
            proxy_iplist.add(ip)
        except:
            _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)
    return proxy_iplist
