#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
import logging
import re
from bs4 import BeautifulSoup,SoupStrainer
from packages import Util as util


_logger = logging.getLogger('proxies')

#每小时更新
__url__ = (
    #'http://code.76lt.com/daili/?dd=gaosu',
    #'http://code.76lt.com/daili/?dd=feiniming',
    #'http://code.76lt.com/daili/?dd=niming',
    #'http://ip.qiaodm.com/free/hot/cn.html',
    #'http://ip.qiaodm.com/free/hot/tw.html',
    #'http://ip.qiaodm.com/free/hot/hk.html',
    #'http://ip.qiaodm.com/free/hot/us.html',
    #'http://ip.qiaodm.com/free/hot/jp.html',
    #'http://ip.izmoney.com/free/foreign-high.html',
    #'http://ip.izmoney.com/free/foreign-normal.html',
    #'http://ip.izmoney.com/free/china-high.html',
    #'http://ip.izmoney.com/free/china-normal.html',
    # 'http://proxy.goubanjia.com/free/gngn/index.shtml',
    # 'http://proxy.goubanjia.com/free/gnpt/index.shtml',
    # 'http://proxy.goubanjia.com/free/gwgn/index.shtml',
    # 'http://proxy.goubanjia.com/free/gwpt/index.shtml',
    'http://www.89ip.cn/tiqu.php?sxb=&tqsl=10000&ports=&ktip=&xl=on',
    'http://www.coobobo.com/free-http-proxy',
    'http://www.ip181.com/',
    'http://xvmlabs.qaulau.net/proxies.txt',
    'http://dev.kuaidaili.com/api/getproxy/?orderid=947980901441522&num=100&b_pcchrome=1&b_pcie=1&b_pcff=1&protocol=1&method=2&an_an=1&an_ha=1&sp1=1&sp2=1&sep=1',
    'http://api.xicidaili.com/free2016.txt',
    'http://www.66ip.cn/getzh.php?getzh=2017062347986&getnum=5000&isp=0&anonymoustype=3&start=&ports=&export=&ipaddress=&area=0&proxytype=1&api=https',
)

_re_compile = None
_re_none = None
_rec = re.compile('([\d]+)')
def fetch_proxy_data(url,**kwargs):
    global _re_compile, _re_none, _rec
    if 'proxies.txt' in url:
        kwargs['timeout'] = 60
    data = fetch(url,**kwargs)
    if not data:
        return False
    proxy_iplist = set()
    if _re_compile is None:
        _re_complie = re.compile('((\d{1,3}\.){3}\d{1,3}:\d{2,6})')
    if '76lt.com' in url or 'proxies.txt' in url or '89ip.cn' in url or \
        'kuaidaili.com' in url or 'xicidaili.com' in url or '66ip.cn' in url:
        match = _re_complie.findall(data)
        for m in match:
            proxy_iplist.add(m[0])
    elif 'goubanjia.com' in url or 'izmoney.com' in url or 'qiaodm.com' in url:
        if 'goubanjia' in url:
            _element_name = 'div'
            _id = 'list'
        elif 'qiaodm.com' in url:
            _element_name = 'div'
            _id = 'main_container'
        else:
            _element_name = 'table'
            _id = 'proxylisttable'
        parse_only = SoupStrainer(_element_name, id=_id)
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find(_element_name, id=_id):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        try:
            proxy_list = bs.find('tbody').find_all('tr')
        except Exception as e:
            print(e)
            proxy_list = None
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            if _re_none is None:
                _re_none = re.compile(r'(<[^<>]+none[^<>]+>[^<>]+</[^<>]+>)')
            try:
                proxy = proxy.find_all('td')
                text = proxy[0].encode()
                nlist = _re_none.findall(text)
                for v in nlist:
                    text = text.replace(v, '')
                _ip = util.strip_tags(text)
                if '.' not in _ip:
                    continue
                if '*' in proxy[1].text:
                    continue
                corval = proxy[1]['class'][-1]
                _pl = []
                for v in corval:
                    _pl.append(str('ABCDEFGHIZ'.index(v)))
                _port = util.number_format(''.join(_pl), 0) >> 3
                ip = '%s:%s' % (
                    _ip, 
                    _port
                )
                proxy_iplist.add(ip)
            except Exception as e:
                print(e)
                _logger.exception('STATUS:407 ; INFO:数据解析异常 ; URL: %s' %  url)      
    elif 'coobobo.com' in url:
        subpage = kwargs.get('subpage', False)
        parse_only = SoupStrainer('table')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False          
        try:
            proxy_list = bs.find('tbody').find_all('tr')
        except Exception as e:
            print(e)
            proxy_list = None
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                dlist = _rec.findall(proxy[0].text)
                if len(dlist) != 4:
                    continue
                ip = '%s:%s' % ('.'.join(dlist), proxy[1].text)
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)    
        if not subpage:
            for i in range(2, 11):
                sub_url = '%s/%s' % (url, i)
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res)  
    elif 'ip181.com' in url:
        parse_only = SoupStrainer('table')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False          
        try:
            proxy_list = bs.find('tbody').find_all('tr')
        except Exception as e:
            print(e)
            proxy_list = None
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                port = util.number_format(proxy[1].text, 0)
                if port <= 0:
                    continue
                ip = '%s:%s' % (proxy[0].text, port)
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL: %s' % url)                      
    return proxy_iplist