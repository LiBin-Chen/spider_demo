# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import math
import logging
from packages import Util

_logger = logging.getLogger('proxies')

'''代理IP，每日更新'''


__url__ = (
    'http://www.ip181.com/daili/1.html',
)


def fetch_proxy_data(url, **kwargs):
    """获取代理数据"""
    data = fetch(url,**kwargs)
    if not data:
        return False
    subpage = kwargs.get('subpage')
    parse_only = SoupStrainer('div', class_='panel-body')
    bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
    if not bs.find('div', class_='panel-body'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    try:
        proxy_list = bs.find('table').find_all('tr')
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
        # 获取分页数
        page_num = 20
        _page = bs.find('div', class_='page')
        if _page:
            _total_num = Util.number_format(_page.text, 0)
            page_num = int(math.ceil(_total_num / 100.0))
        print('正在获取分页数据，共有 %s 个分页...' % (page_num, ))
        if page_num > 1:
            for i in range(2, page_num + 1):
                sub_url = '%s/%s.html' % ('http://www.ip181.com/daili', i)
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res)
    return proxy_iplist