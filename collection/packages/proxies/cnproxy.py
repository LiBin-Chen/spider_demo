#!/usr/bin/env python
# -*- encoding: utf-8 -*-




from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging
from packages import Util

_logger = logging.getLogger('proxies')

__url__ = (
    'http://cn-proxy.com/',
)

def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    data = fetch(url, **kwargs)
    if not data:
        return False
    parse_only = SoupStrainer('div',id = 'container')
    bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
    if not bs:
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    proxy_data = bs.find_all('table',class_ ='sortable')
    if not proxy_data:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False

    proxy_iplist = set()
    for proxy_list in proxy_data:
        proxy_list = proxy_list.find('tbody').find_all('tr')
        if not proxy_list:
            continue
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                _proxy_scheme = ''
                _type = Util.cleartext(proxy[4].get_text()).lower()
                if _type in ('socks4','socks5'):
                    _proxy_scheme = '%s://' % _type
                ip = '%s%s:%s' % (_proxy_scheme,Util.cleartext(proxy[0].get_text()),Util.cleartext(proxy[1].get_text()))
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
    return proxy_iplist