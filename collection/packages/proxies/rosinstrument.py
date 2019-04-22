#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup,SoupStrainer
import re
import math
import logging
from packages import Util

_logger = logging.getLogger('proxies')

__url__ = (
    'http://rosinstrument.com/raw_free_db.htm?t=1',
)


_re_compile = None

def fetch_proxy_data(url,**kwargs):
    '''
    获取代理数据
    '''
    global _re_compile
    data = fetch(url,**kwargs)
    if not data:
        _logger.info('STATUS:404 ; INFO:无数据 ; URL: %s' % url)
        return False
    if _re_compile is None:
        _re_compile = re.compile("Math\.sqrt\((\d+)\)[\s\S]+hideTxt\(\s*\'([\d\D]+)\'\s*\);\s*-->")
    match = _re_compile.findall(data)
    if not match:
        _logger.exception('STATUS:405 ; INFO:数据解析异常 ; URL: %s' % url)
        return False
    x = int(math.ceil(math.sqrt(int(match[0][0]))))
    data = Util.urldecode(match[0][1])
    text = ''
    i = 0
    for s in data:
        t = ord(s) ^ (x if i % 2 else 0)
        text += chr(t)
        i += 1
    ip_list = re.findall('\|([\s\S]+?)\^',text)
    if not ip_list:
        _logger.exception('STATUS:405 ; INFO:数据解析异常 ; URL: %s' % url)
        return False
    proxy_iplist = set()
    for ip in ip_list:
        try:
            ip = _parse_data(ip)
            ip and proxy_iplist.add(ip)
        except:
            _logger.exception('STATUS:405 ; INFO:数据解析异常 ; URL: %s' % url)

    subpage = kwargs.get('subpage',False)
    if not subpage:
        match = re.search('<a\shref=\'\?(\d+)[^<>]+title=\'[^<>]+last',text)
        page_num = 1
        if match:
            page_num = int(match.group(1))
        if page_num > 1:
            kwargs['subpage'] = True
            for p in range(2,page_num + 1):
                sub_url = 'http://rosinstrument.com/raw_free_db.htm?%s&t=1' % p
                res = fetch_proxy_data(sub_url,**kwargs)
                res and proxy_iplist.update(res)
    return proxy_iplist

_re_compile_ip = None
_re_compile_sub = None
def _parse_data(data):
    '''
    解析数据获取ip
    '''
    global _re_compile_ip,_re_compile_sub
    if _re_compile_ip is None:
        _re_compile_ip = re.compile('&#(\d{1,3});')
    mlist = _re_compile_ip.findall(data)
    for m in mlist:
        data = data.replace('&#%s;' % m,chr(int(m)))
    if _re_compile_sub is None:
        _re_compile_sub = re.compile(':[^\d]*.*[^\d]+')
    return _re_compile_sub.sub(':',data).replace('%','.')