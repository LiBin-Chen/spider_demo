#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__author__ = 'qaulau'

from .__init__ import fetch
from bs4 import BeautifulSoup,SoupStrainer
import re
import logging

_logger = logging.getLogger('proxies')

__url__ = (
    'http://txt.proxyspy.net/proxy.txt',
)


_re_compile = None
def fetch_proxy_data(url,**kwargs):
    '''
    获取代理数据
    '''
    global _re_compile
    data = fetch(url,**kwargs)
    proxy_iplist = set()
    if _re_compile is None:
        _re_complie = re.compile('((\d{1,3}\.){3}\d{1,3}:\d{2,6})')
    match = _re_complie.findall(data)
    for m in match:
        proxy_iplist.add(m[0])

    return proxy_iplist