#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup,SoupStrainer
import re
import logging

_logger = logging.getLogger('proxies')

__url__ = (
    'http://www.mesk.cn/sitemap.xml',
)

_re_compile = None
def fetch_proxy_data(url,**kwargs):
    '''
    获取代理数据
    '''
    global _re_compile
    data = fetch(url,**kwargs)
    if not data:
        return False
    proxy_iplist = set()
    if 'sitemap.xml' in url:
        bs = BeautifulSoup(data,'lxml')
        url_list = bs.find_all('url',limit = 44)
        if not url_list:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        for url in url_list:
            url = url.find('loc').get_text()
            if re.search(r'([china|hongkong|europe|foreign][\d{4}/]{3})',url):
                res = fetch_proxy_data(url)
                res and proxy_iplist.update(res)
    else:
        parse_only = SoupStrainer('div',class_ = 'article mt10')
        bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
        if not bs.find('div',class_ = 'article mt10'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        article = bs.find('div',class_ = 'article')
        if not article:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        if _re_compile is None:
            _re_compile = re.compile('((\d{1,3}\.){3}\d{1,3}:\d{2,6})')
        match = _re_compile.findall(article.get_text())
        for m in match:
            proxy_iplist.add(m[0])
    return proxy_iplist