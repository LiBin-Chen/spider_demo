#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import logging
from packages import Util
_logger = logging.getLogger('proxies')

__url__ = (
    'http://www.xicidaili.com/nn/', #有效率低，百分之十以下，下同
    'http://www.xicidaili.com/nt/',
    'http://www.xicidaili.com/wt/',
    'http://www.xicidaili.com/wn/',
)

_headers = {
    'Host':'www.xicidaili.com',
    'user-agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
}

_cookies = None

def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    global _cookies
    data = fetch(url,headers = _headers,cookies= _cookies,**kwargs)
    if not data:
        _logger.info('STATUS:404 ; INFO:无数据 ; URL: %s' % url)
        return False

    bs = BeautifulSoup(data, 'lxml')
    ip_list = bs.find('table', id='ip_list')
    if not ip_list:
        try:
            _iframe = bs.find('iframe')
            _count = kwargs.get('count',0)
            if _count < 3 and _iframe:
                _url = 'http://www.xici.net.co/' + _iframe['src']
                rs = fetch(_url,headers=_headers,return_response = True)
                _cookies = rs.cookies
                return fetch_proxy_data(url,count = _count,**kwargs)
        except:
            pass
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False

    proxy_iplist = set()
    proxy_list = ip_list.find_all('tr')
    if not proxy_list:
        _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False
    del proxy_list[0]
    for proxy in proxy_list:
        try:
            proxy = proxy.find_all('td')
            ip = '%s:%s' % (Util.cleartext(proxy[1].text, ' '), Util.cleartext(proxy[2].text, ' '))
            proxy_iplist.add(ip)
        except Exception as  e:
            _logger.exception('%s ; URL:%s' % (Util.traceback_info(e), url))

    subpage = kwargs.get('subpage',False)
    if not subpage:
        #获取前10页数据（避免过期数据）
        print('正在获取分页数据...')
        for i in range(2, 11):
            sub_url = '%s%s' % (url, i)
            res = fetch_proxy_data(sub_url, subpage=True)
            res and proxy_iplist.update(res)
    return proxy_iplist