#!/usr/bin/env python
# -*- encoding: utf-8 -*-



import sys
import re
import logging
import requests

import config
from packages import Util as util


__all__ = [
    'pachong',
    'mesk',
    'kuaidaili',
    #'nntime', js
    'rosinstrument',
    'idcloak',
    'cz88',
    'p76lt',
    'didsoft',
    'cnproxy',
    'ip181',
    'xici',
    'samair',
    'other'
]




_logger = logging.getLogger('proxies')


def fetch(url, post_data=None, headers=None, **kwargs):
    '''
    获取代理数据
    '''
    if headers:
        _headers = headers
    else:
        _headers = {
            'user-agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
        }
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 45)
    _page = ''
    if 'page' in kwargs:
        _page = '; Page : %s' % kwargs['page']
    if not kwargs.get('hide_print',False):
        print('Fetch URL ：%s %s' % (url, _page))

    try:
        http_method = 'GET' if post_data is None else 'POST'
        rs = requests.request(http_method, url, data=post_data, headers=_headers, cookies=cookies,
                              proxies=proxies, timeout=timeout)
    except Exception as e:
        _logger.info('请求异常 ; %s' % (e, ))
        return None

    if rs.status_code != 200:
        _logger.debug('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
        return None
    if 'return_response' in kwargs:
        return rs
    return rs.text


def check_proxy(ip, data_list=[], error=0):
    """检测代理"""
    timeout = 15
    headers = {
        'user-agent': 'HQCHIP Crawler/1.0 +http://www.hqchip.com'
    }
    if 'socks' not in ip:
        proxies = {'http': 'http://' + ip}
    else:
        proxies = {'http': ip}
    #检测是否可用和是否是高匿带代理，返回{"statue":1}是高匿代理
    print('Check IP : %s' % ip)
    res = fetch('http://proxy.elecfans.net/', proxies=proxies, headers=headers,
                        timeout=timeout, hide_print=True)
    try:
        if res:
            data = json.loads(res)
            status = int(data['statue'])
        else:
            status = None
    except Exception as e:
        #_logger.exception('检测异常')
        status = None
    data_list.append((ip,status,error))
    return status


_re_letter = None
def check_proxy_ip(ip):
    '''检测代理IP
    对于没有端口或者端口

    :param ip:
    :return:
    '''
    global _re_letter
    if not ip:
        return False
    try:
        _proxy_scheme, _proxy_host, _proxy_port = util.get_host(ip)
    except:
        return False
    if _re_letter is None:
        _re_letter = re.compile('[^0-9]+')
    if not _proxy_port or _re_letter.search(str(_proxy_port)):
        return False
    if not _proxy_host:
        return False
    _host = _proxy_host.split('.')[-1]
    if _re_letter.search(_host) and _host not in ('com', 'net', 'cn', 'org', 'us', 'jp', 'tw', 'me'):
        return False
    return True 