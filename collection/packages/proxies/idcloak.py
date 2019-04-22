#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging
from packages import Util

_logger = logging.getLogger('proxies')

'''
idcloak免费代理IP，每天更新

含部分 socks 代理，共有400 - 700 个代理
'''
__url__ = (
    'http://www.idcloak.com/proxylist/proxy-list.html',
)

def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    post_data = {
       'country': 'XY',
       'port[]' : 'all',
       'protocol-http' : 'true',
       'protocol-https' : 'true',
       'protocol-socks4' : 'true',
       'protocol-socks5' : 'true',
       'anonymity-low' : 'true',
       'anonymity-medium' : 'true',
       'anonymity-high' : 'true',
       'connection-low' : 'true',
       'connection-medium' : 'true',
       'connection-high' : 'true',
       'speed-low' : 'true',
       'speed-medium':'true',
       'speed-high':'true',
       'order':'desc',
       'by':'updated',
    }
    page = kwargs.get('page',1)
    if page > 1:
        post_data['page'] = page
    kwargs['page'] = page
    data = fetch(url, post_data=post_data,**kwargs)
    if not data:
        return False
    parse_only = SoupStrainer('form', id='proxy-search')
    bs = BeautifulSoup(data,'lxml',parse_only=parse_only)
    if not bs.find('form', id='proxy-search'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False

    try:
        proxy_list = bs.find('table', id='sort').find_all('tr')
    except:
        _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)
        return False
    if not proxy_list:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False

    proxy_iplist = set()
    del proxy_list[0]
    for proxy in proxy_list:
        try:
            proxy = proxy.find_all('td')
            if not proxy:
                continue
            _proxy_scheme = ''
            _type = Util.cleartext(proxy[5].text).lower()
            if _type in ('socks4','socks5'):
                _proxy_scheme = '%s://' % _type
            ip = '%s%s:%s' % (_proxy_scheme,proxy[7].text, proxy[6].text)
            proxy_iplist.add(ip)
        except Exception as  e:
            _logger.exception('%s ; URL:%s' % (Util.traceback_info(e), url))

    if page == 1:
        try:
            page_list = bs.find('div',class_ = 'pagination').find_all('input')
            page_num = len(page_list)
        except:
            page_num = 1

        if page_num > 1:
            for i in range(1,page_num):
                kwargs['page'] = i + 1
                res = fetch_proxy_data(url,**kwargs)
                res and proxy_iplist.update(res)
    return proxy_iplist