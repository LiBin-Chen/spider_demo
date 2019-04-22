#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import re
import logging
from packages import Util

_logger = logging.getLogger('proxies')

__url__ = (
    'http://www.kuaidaili.com/proxylist/',
    'http://www.kuaidaili.com/free/inha/',
    'http://www.kuaidaili.com/free/intr/',
    'http://www.kuaidaili.com/free/outha/',
    'http://www.kuaidaili.com/free/outtr/'
)

def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    data = fetch(url,**kwargs)
    if not data:
        return False
    subpage = kwargs.get('subpage',False)
    _id = 'index_free_list' if '/proxylist/' in url else 'list'
    parse_only = SoupStrainer('div', id='index_free_list')
    bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
    if not bs.find('div', id='index_free_list'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    try:
        proxy_list = bs.find('tbody').find_all('tr')
    except:
        _logger.exception('STATUS:405 ; INFO:元素解析错误 ; URL:%s' % url)
        return False
    if not proxy_list:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False

    proxy_iplist = set()
    for proxy in proxy_list:
        try:
            proxy = proxy.find_all('td')
            ip = '%s:%s' % (proxy[0].get_text(), proxy[1].get_text())
            proxy_iplist.add(ip)
        except Exception as e:
            _logger.exception('%s ; URL:%s' % (Util.traceback_info(e), url))

    if not subpage:
        #获取分页数, 这家含有很多很久以前的数据只获取10页
        page_num = 10
        print('正在获取分页数据，共有 %s 个分页...' % page_num)
        if page_num > 1:
            for i in range(2, page_num + 1):
                sub_url = '%s%s' % (url, i)
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res)
    return proxy_iplist