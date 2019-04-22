#!/usr/bin/env python
# -*- encoding: utf-8 -*-


from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import re
import logging
from packages import Util

_logger = logging.getLogger('proxies')

__url__ = (
    'http://pachong.org/anonymous.html',
    'http://pachong.org/transparent.html',
    # 'http://pachong.org/socks.html'
)

__timeout__ = 5


def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    data = fetch(url, **kwargs)
    if not data:
        return False

    parse_only = SoupStrainer('div', class_='mainWap')
    bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)

    if not bs.find('div', class_='mainWap'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    try:
        proxy_list = bs.find('tbody').find_all('tr')
    except:
        _logger.exception('STATUS:406 ; INFO:元素解析错误 ; URL:%s' % url)
        return False
    if not proxy_list:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False
    proxy_iplist = set()
    for proxy in proxy_list:
        try:
            proxy = proxy.find_all('td')
            _proxy_scheme = ''
            _type = Util.cleartext(proxy[4].get_text()).lower()
            if _type in ('socks4', 'socks5'):
                _proxy_scheme = '%s://' % _type
            ip = '%s%s:%s' % (_proxy_scheme, proxy[1].get_text(), Util.number_format(proxy[2].get_text(), 0))
            proxy_iplist.add(ip)
        except Exception as e:
            _logger.exception('%s ; URL:%s' % (Util.traceback_info(e), url))
    return proxy_iplist
