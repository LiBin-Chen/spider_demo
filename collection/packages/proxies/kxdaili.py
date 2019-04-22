#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import re
import logging
from packages import Util

_logger = logging.getLogger('proxies')

__url__ = (
    'http://api.kxdaili.com/?api=20151110200040011100750070720170&pw=123456&dengji=%E9%AB%98%E5%8C%BF&checktime=30%E5%88%86%E9%92%9F%E5%86%85&sleep=15%E7%A7%92%E5%86%85&ct=1000',
)
_re_compile = None


def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    global _re_compile
    data = fetch(url,**kwargs)
    if not data:
        return False
    if _re_compile is None:
        _re_compile = re.compile('((\d{1,3}\.){3}\d{1,3}:\d{2,6})')
    proxy_iplist = set()
    match = _re_compile.findall(data)
    for m in match:
        proxy_iplist.add(m[0])
    return proxy_iplist
    