#!/usr/bin/env python
# -*- encoding: utf-8 -*-


from packages import Util
from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging

_logger = logging.getLogger('proxies')

'''
纯真HTTP代理IP，每日更新
'''
__url__ = (
    'http://www.cz88.net/proxy/index.shtml',
    'http://www.cz88.net/proxy/http_2.shtml',
    'http://www.cz88.net/proxy/http_3.shtml',
    'http://www.cz88.net/proxy/http_4.shtml',
    'http://www.cz88.net/proxy/http_5.shtml',
    'http://www.cz88.net/proxy/http_6.shtml',
    'http://www.cz88.net/proxy/http_7.shtml',
    'http://www.cz88.net/proxy/http_8.shtml',
    'http://www.cz88.net/proxy/http_9.shtml',
    'http://www.cz88.net/proxy/http_10.shtml',
    # socks代理
    # 'http://www.cz88.net/proxy/socks4.shtml',
    # 'http://www.cz88.net/proxy/socks4_2.shtml',
    # 'http://www.cz88.net/proxy/socks4_3.shtml',
    # 'http://www.cz88.net/proxy/socks5.shtml',
    # 'http://www.cz88.net/proxy/socks5_2.shtml',
)


def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    data = fetch(url, **kwargs)
    if not data:
        return False
    parse_only = SoupStrainer('div', id='boxright')
    bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
    if not bs.find('div', id='boxright'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    ip_list = bs.find_all('li')
    if not ip_list:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False
    _proxy_scheme = ''
    if 'socks4' in url:
        _proxy_scheme = 'socks4://'
    elif 'socks5' in url:
        _proxy_scheme = 'socks5://'
    proxy_iplist = set()
    for ip in ip_list:
        if not ip.find('div', class_='ip'):
            continue
        try:
            proxy = ip.find_all('div')
            ip = '%s%s:%s' % (_proxy_scheme, Util.cleartext(proxy[0].get_text()), Util.cleartext(proxy[1].get_text()))
            proxy_iplist.add(ip)
        except:
            _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
    return proxy_iplist
