#!/usr/bin/env python
# -*- encoding: utf-8 -*-



from .__init__ import fetch
from bs4 import BeautifulSoup,SoupStrainer
import re
import logging
import math
import time

try:
    import json
except ImportError:
    import simplejson as json
from packages import Util

try:
    from Crypto.Cipher import AES
except:
    AES = None

_logger = logging.getLogger('proxies')

'''
一些可以简单获取代理数据的站点，分成单独模块显得过于浪费
'''
__url__ = (
    #'http://japi.juheapi.com/japi/fatch?key=8fcc80ea91baf429cc7a241f1f556f43',  # 100个代理IP
    #'http://apis.haoservice.com/devtoolservice/ipagency?key=e6bb001b83c24777924e528ce2bb3595',
    'http://checkerproxy.net/getAllProxyByDay', # 大约2000+个
    'http://www.89ip.cn/tiqu.php?sxb=&tqsl=10000&ports=&ktip=&xl=on',
    'http://m.66ip.cn/nmtq.php?getnum=800&isp=0&anonymoustype=1&start=&ports=&export=&ipaddress=&area=0&proxytype=2&api=66ip',
    'http://m.66ip.cn/nmtq.php?getnum=800&isp=0&anonymoustype=2&start=&ports=&export=&ipaddress=&area=0&proxytype=2&api=66ip',
    'http://m.66ip.cn/nmtq.php?getnum=800&isp=0&anonymoustype=3&start=&ports=&export=&ipaddress=&area=0&proxytype=2&api=66ip',
    'http://m.66ip.cn/nmtq.php?getnum=800&isp=0&anonymoustype=4&start=&ports=&export=&ipaddress=&area=0&proxytype=2&api=66ip',
    #'http://www.echolink.org/proxylist.jsp',
    'http://proxyservers.pro/proxy/list/order/updated/order_dir/desc/page',
    'http://proxydb.net/list',      # 6000+
    'https://www.hide-my-ip.com/proxylist.shtml',
    'http://ip84.com/gn',
    'http://ip84.com/pn',
    'http://ip84.com/tm',
    'http://ip84.com/gw',
    'http://www.mimiip.com/gngao',
    'http://www.mimiip.com/gnpu',
    'http://www.mimiip.com/gntou',
    'http://www.mimiip.com/hw',
    'http://www.yun-daili.com/free.asp?stype=1',
    'http://www.yun-daili.com/free.asp?stype=2',
    'http://www.yun-daili.com/free.asp?stype=3',
    'http://www.yun-daili.com/free.asp?stype=4',
    'http://txt.proxyspy.net/proxy.txt',
    'http://www.youdaili.net/Daili/http/',
    'http://www.youdaili.net/Daili/guonei/',
    'http://www.youdaili.net/Daili/guowai/',
    'http://www.youdaili.net/Daili/Socks/',
    #'http://www.xunluw.com/IP/index.html',
    'http://letushide.com/filter/all,all,all/list_of_free_proxy_servers',
    'http://proxy.ipcn.org/proxylist.html',
    'http://proxy.ipcn.org/proxylist2.html',
    'http://www.china-proxy.org/proxylist',
    'http://www.site-digger.com/html/articles/20110516/proxieslist.html',
    'http://ip.shifengsoft.com/get.php?tqsl=10000', # 大约5000左右
    'http://ip.qqroom.cn/',                         # 大约 3000 多个
    'http://www.89ip.cn/api/?&tqsl=10000&sxa=&sxb=&tta=&ports=&ktip=&cf=1', # 2300+个
    'http://www.haodailiip.com/guonei',             # 3000+
    'http://www.haodailiip.com/guoji',              # 3000+
    'http://www.ip3366.net/free/?stype=1',          # 400左右
    'http://www.ip3366.net/free/?stype=2',
    'http://www.ip3366.net/free/?stype=3',
    'http://www.ip3366.net/free/?stype=4',
    'http://www.nianshao.me/?stype=1',              # 2000 + 
)


_re_compile = None
def fetch_proxy_data(url,**kwargs):
    '''
    获取代理数据
    '''
    global _re_compile
    rs = fetch(url, return_response=1, **kwargs)
    if not rs:
        return False
    data = rs.text
    if not data:
        return False
    subpage = kwargs.get('subpage',False)
    proxy_iplist = set()
    if _re_compile is None:
        _re_compile = re.compile('((\d{1,3}\.){3}\d{1,3}:\d{2,6})')

    if 'juheapi.com' in url or 'haoservice.com' in url or 'proxyspy.net' in url: 
        match = _re_compile.findall(data)
        for m in match:
            proxy_iplist.add(m[0])
    elif 'checkerproxy.net' in url:
        parse_only = SoupStrainer('div',class_='main')
        bs = BeautifulSoup(data,'lxml', parse_only=parse_only)
        if not bs.find('div', class_='main'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        if 'getAllProxyByDay' in url:
            url_list = bs.find_all('a')
            if not url_list:
                _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
                return False
            #仅获取前10个链接
            url_list = url_list[0:10]
            for url in url_list:
                try:
                    url = 'http://checkerproxy.net%s' % (url['href'] if url['href'][0] == '/' else url['href'] + '/', )
                    res = fetch_proxy_data(url)
                    res and proxy_iplist.update(res)
                except:
                    _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
        else:
            match = _re_compile.findall(bs.encode())
            for m in match:
                proxy_iplist.add(m[0])
    elif 'youdaili.net' in url:
        if '.html' in url:
            parse_only = SoupStrainer('div',class_ = 'content')
            bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
            if not bs.find('div',class_ = 'content'):
                _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
                return False
            match = _re_compile.findall(bs.get_text())
            _proxy_scheme = ''
            if 'Socks' in url:
                _proxy_scheme = 'socks4://'
            for m in match:
                proxy_iplist.add(_proxy_scheme + m[0])
            return proxy_iplist
        parse_only = SoupStrainer('ul',class_ = 'newslist_line')
        bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
        if not bs.find('ul',class_ = 'newslist_line'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        url_list = bs.find_all('a')
        if not url_list:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        #仅获取前10个链接
        url_list = url_list[0:10]
        for url in url_list:
            try:
                res = fetch_proxy_data(url['href'])
            except:
                _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            res and proxy_iplist.update(res)
    elif 'qqroom.cn' in url:
        if '.html' in url:
            match = _re_compile.findall(data)
            for m in match:
                proxy_iplist.add(m[0])
            return proxy_iplist
        parse_only = SoupStrainer('article', class_='recent-posts')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('article', class_='recent-posts'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        url_list = bs.find_all('a')
        if not url_list:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        #仅获取前10个链接
        url_list = url_list[0:10]
        for row in url_list:
            try:
                _url = Util.urljoin(url, row['href'])
                res = fetch_proxy_data(_url)
            except:
                _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % (url, ))
            res and proxy_iplist.update(res)
    elif 'xunluw.com' in url:
        if 'index.html' not in url:
            parse_only = SoupStrainer('div',id = 'Article')
            bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
            if not bs.find('div',id = 'Article'):
                _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
                return False
            match = _re_compile.findall(bs.get_text())
            for m in match:
                proxy_iplist.add(m[0])
            return proxy_iplist
        parse_only = SoupStrainer('div',class_ = 'col-left')
        bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
        if not bs.find('div',class_ = 'col-left'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        url_list = bs.select('li > a')
        if not url_list:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        #仅获取前10条链接的数据
        url_list = url_list[0:10]
        for url in url_list:
            try:
                res = fetch_proxy_data(url['href'])
            except:
                _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            res and proxy_iplist.update(res)

    elif 'letushide.com' in url:
        parse_only = SoupStrainer('div',id = 'data')
        bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
        if not bs.find('div',id = 'data'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        proxy_list = bs.find_all('tr',id = 'data')
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                ip = '%s:%s' % (proxy[1].get_text(), proxy[2].get_text())
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:407 ; INFO:数据解析异常 ; URL: %s' %  url)
        if not subpage:
            #获取分页数
            count = bs.find('div',class_ = 'count')
            page_num = 1
            if count:
                total_count = Util.number_format(count.get_text(),0)
                page_num = int(math.ceil(total_count / 24.0))
            print('正在获取分页数据，共有 %s 个分页...' % page_num)
            if page_num > 1:
                for i in range(2, page_num + 1):
                    sub_url = '%s/%s/list_of_free_proxy_servers' % ('http://letushide.com/filter/all,all,all', i)
                    res = fetch_proxy_data(sub_url, subpage=True)
                    res and proxy_iplist.update(res)
    elif 'ipcn.org' in url or 'china-proxy.org' in url or 'shifengsoft' in url or \
         '89ip.cn' in url or '66ip.cn' in url or 'www.89ip.cn' in url:
        match = _re_compile.findall(data)
        for m in match:
            proxy_iplist.add(m[0])
    elif 'site-digger.com' in url:
        if AES is None:
            print('请安装 PyCrypto 模块')
            return False
        aes_key = 'a5b3dbf810d011e5'
        match = re.search('baidu_union_id\s=\s"([\w]+)"', data)
        if match:
            aes_key = match.group(1)
        parse_only = SoupStrainer('table', id='proxies_table')
        bs = BeautifulSoup(data,'lxml',parse_only = parse_only)
        if not bs.find('table', id='proxies_table'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        try:
            proxy_list = bs.find('tbody').find_all('tr')
        except:
            proxy_list = None
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                ip = _decrypt_proxy_ip(proxy[0].get_text(), aes_key)
                ip and proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:407 ; INFO:数据解析异常 ; URL: %s' %  url)
    elif 'haodailiip.com' in url:
        parse_only = SoupStrainer('table', class_='proxy_table')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table', class_='proxy_table'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        proxy_list = bs.find_all('tr')
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                _ip = Util.cleartext(proxy[0].text, ' ')
                if '.' not in _ip:
                    continue
                ip = '%s:%s' % (
                    _ip, 
                    Util.cleartext(proxy[1].text, ' ')
                )
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:407 ; INFO:数据解析异常 ; URL: %s' %  url)
        if not subpage:
            _cookies = {}
            for vo in rs.cookies:
                _cookies[vo.name] = vo.value
            _ptype = 'guonei' if 'guonei' in url else 'guoji'
            if proxy_iplist:
                time.sleep(1)
            for i in range(2, 101):
                sub_url = '%s/%s/%s' % ('http://www.haodailiip.com', _ptype, i)
                res = fetch_proxy_data(sub_url, subpage=True, cookies=_cookies)
                if res:
                    proxy_iplist.update(res)
                    time.sleep(1)
                else:
                    break
    elif 'ip3366.net' in url or 'www.yun-daili.com' in url:
        parse_only = SoupStrainer('div', id='list')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('div', id='list'):
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
                _ip = Util.cleartext(proxy[0].text, ' ')
                if '.' not in _ip:
                    continue
                ip = '%s:%s' % (
                    _ip, 
                    Util.cleartext(proxy[1].text, ' ')
                )
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:407 ; INFO:数据解析异常 ; URL: %s' %  url)
        if not subpage:
            for i in range(2, 8):
                sub_url = '%s&page=%s' % (url, i)
                res = fetch_proxy_data(sub_url, subpage=True)
                if res:
                    proxy_iplist.update(res)
                    time.sleep(1)
                else:
                    break
    elif 'nianshao.me' in url:
        parse_only = SoupStrainer('table', class_='table')
        bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
        if not bs.find('table', class_='table'):
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        try:
            proxy_list = bs.find('tbody').find_all('tr')
        except:
            proxy_list = []
        if not proxy_list:
            _logger.info('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                _ip = Util.cleartext(proxy[0].text, ' ')
                if '.' not in _ip:
                    continue
                ip = '%s:%s' % (
                    _ip, 
                    Util.cleartext(proxy[1].text, ' ')
                )
                proxy_iplist.add(ip)
            except:
                _logger.exception('STATUS:407 ; INFO:数据解析异常 ; URL: %s' %  url)
        if not subpage:
            for i in range(2, 101):
                sub_url = '%s&page=%s' % (url, i)
                res = fetch_proxy_data(sub_url, subpage=True)
                if res:
                    proxy_iplist.update(res)
                    time.sleep(1)
                else:
                    break     
    elif 'ip84.com' in url or 'www.mimiip.com' in url:
        bs = BeautifulSoup(data, 'lxml')
        ip_list = bs.find('table', class_='list')
        if not ip_list:
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
                if not proxy:
                    continue
                ip = '%s:%s' % (Util.cleartext(proxy[0].text, ' '), Util.cleartext(proxy[1].text, ' '))
                proxy_iplist.add(ip)
            except Exception as e:
                _logger.exception('%s ; URL:%s' % (Util.traceback_info(e), url))

        subpage = kwargs.get('subpage',False)
        if not subpage:
            #获取前10页数据（避免过期数据）
            print('正在获取分页数据...')
            for i in range(2, 11):
                sub_url = '%s/%s' % (url, i)
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res) 
    elif 'www.hide-my-ip.com' in url:
        proxy_iplist = set()
        match = re.search('var\sjson\s=([^;]+);', data)
        if match:
            try:
                iplist = json.loads(match.group(1).replace(' ', '').replace("\n", '')) 
                for vo in iplist:
                    ip = '%s:%s' % (Util.cleartext(vo['i'], ' '), Util.cleartext(vo['p'], ' '))
                    proxy_iplist.add(ip)
            except Exception as e:
                _logger.exception('解析异常 ; URL:%s' % (url,))
    elif 'proxydb.net' in url or 'proxyservers.pro' in url:
        bs = BeautifulSoup(data, 'lxml')
        ip_list = bs.find('table', class_='table-responsive')
        if not ip_list:
            _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
            return False

        proxy_iplist = set()
        try:
            proxy_list = ip_list.find('tbody').find_all('tr')
        except:
            proxy_list = None
        if not proxy_list:
            _logger.info('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
            return False
        for proxy in proxy_list:
            try:
                proxy = proxy.find_all('td')
                if not proxy:
                    continue
                proxy_iplist.add(Util.cleartext(proxy[0].text, ' '))
            except Exception as  e:
                _logger.exception('解析proxydb异常 ; URL:%s' % (url, ))

        subpage = kwargs.get('subpage')
        if not subpage:
            print('正在获取分页数据...')
            pn = 15 if 'proxyservers.pro' in url else 100
            for i in range(2, pn):
                sub_url = '%s/?offset=%s' % (url, (i-1)*25)
                res = fetch_proxy_data(sub_url, subpage=True)
                res and proxy_iplist.update(res)  
    return proxy_iplist


_re_decrypt_compile = None
def _decrypt_proxy_ip(text, k):
    '''解密代理信息'''
    global _re_decrypt_compile, _re_compile
    if not text:
        return None
    if _re_decrypt_compile is None:
        _re_decrypt_compile = re.compile('decrypt\("([^\s]+)"\)')

    if _re_compile is None:
        _re_compile = re.compile('((\d{1,3}\.){3}\d{1,3}:\d{2,6})')
    match = _re_decrypt_compile.search(text)
    if match:
        decrypt_info = match.group(1).strip('')
        obj = AES.new(k, AES.MODE_CBC, k)
        proxy_ip = obj.decrypt(decrypt_info.decode('base64'))
        match = _re_compile.search(proxy_ip)
        if match:
            return match.group(1)
    return None