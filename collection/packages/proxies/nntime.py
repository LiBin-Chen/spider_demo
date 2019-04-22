#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging
from packages import Util
import re

_logger = logging.getLogger('proxies')

#有一千多个代理IP
__url__ = (
    'http://nntime.com/proxy-ip-01.htm',
)

_re_compile = None
_re_compile_var = None

def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    data = fetch(url,**kwargs)
    if not data:
        return False
    bs = BeautifulSoup(data,'lxml')
    if not bs.find('div', id='main'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    var_list = _parse_data(data,url)
    if not var_list:
        _logger.warning('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
        return False
    var1 = var_list[0][0]
    var2 = var_list[0][1]
    try:
        proxy_list = bs.find('table',id = 'proxylist').find_all('tr')
    except:
        _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)
        return False

    proxy_iplist = set()
    for proxy in proxy_list:
        proxy = proxy.find('input',attrs = {'type':'checkbox'})
        if not proxy:
            continue
        proxy = proxy['value']
        if not proxy:
            continue
        proxy = proxy.replace(var1,'').replace(var2,':')
        proxy_iplist.add(proxy)

    subpage = kwargs.get('subpage',False)
    if not subpage:
        try:
            page_list = bs.find('div',id = 'navigation').find_all('a')
            del page_list[-1]
            for p in page_list:
                sub_url = 'http://nntime.com/' + p['href']
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res)
        except Exception as e:
            _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)
    return proxy_iplist

_var_list = []
def _parse_data(data,url,**kwargs):
    '''
    解析数据,获取js变量值项
    '''
    global _re_compile,_re_compile_var,_var_list
    if _re_compile is None:
        _re_compile = re.compile('<script\ssrc="([^<>"]+)"[^<>]+></script>')
    match = _re_compile.search(data)
    if not match:
        _logger.exception('数据解析异常 ; URL: %s' % url)
        return False
    js_url = 'http://nntime.com/' + Util.cleartext(match.group(1),' ')
    if _var_list and _var_list[1] == js_url:
        return _var_list[0]
    if 'headers' not in kwargs:
        kwargs['headers'] = {'referer':url}
    else:
        kwargs['headers']['referer'] = url
    data = fetch(js_url,**kwargs)
    if not data:
        return False
    if _re_compile_var is None:
        _re_compile_var = re.compile('([\d]+)[^\d]*\|forms\|[^\d]*([\d]+)')
    var_list = _re_compile_var.findall(data)
    if var_list:
        _var_list = [var_list[0],js_url]
    return var_list