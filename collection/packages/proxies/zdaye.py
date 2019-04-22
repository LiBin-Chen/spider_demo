#!/usr/bin/env python
# -*- encoding: utf-8 -*-


from .__init__ import fetch
from bs4 import BeautifulSoup, SoupStrainer
import re
import logging
from packages import Util
import hashlib

_logger = logging.getLogger('proxies')

'''
这家可以获取两千多个代理IP，都是几分钟更新一次
但需要注意关注是否更新的防采集策略
'''
__region__ = ('电信', '联通', '移动', '大学', '美国', '日本', '韩国', '澳门', '香港', '台湾', '新加坡', '印度', '韩国', '北京', '天津',
              '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北',
              '湖南', '广东', '甘肃', '四川', '贵州', '海南', '云南', '青海', '陕西', '广西', '西藏', '宁夏', '新疆', '内蒙')

__url__ = tuple(['http://ip.zdaye.com/?adr=%s' % Util.urlencode(r.decode('utf-8').encode('gbk')) for r in __region__])

del __region__

__headers__ = {
    'user-agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
    'Host': 'ip.zdaye.com',
}

__timeout__ = 3


def fetch_proxy_data(url, **kwargs):
    '''
    获取代理数据
    '''
    rs = fetch(url, return_response=True, headers=__headers__, **kwargs)
    try:
        data = rs.text
        cookies = rs.cookies
    except:
        return False
    if not data:
        _logger.info('STATUS:404 ; INFO:无数据 ; URL: %s' % url)
        return False
    parse_only = SoupStrainer('table', id='ipc')
    bs = BeautifulSoup(data, 'lxml', parse_only=parse_only)
    if not bs.find('table', id='ipc'):
        _logger.warning('STATUS:405 ; INFO:数据请求异常 ; URL:%s' % url)
        return False
    proxy_list = bs.find_all('tr')
    if not proxy_list:
        _logger.warning('STATUS:404 ; INFO:没有数据 ; URL:%s' % url)
        return False
    proxy_iplist = set()
    try:
        var_dict = _get_var_dict(url, cookies=cookies, headers=__headers__)
        var_rev = _get_revised_var(url, cookies=cookies, mk=var_dict['mk'], ak=var_dict['ak'], headers=__headers__)
    except:
        _logger.exception('STATUS:410 ; INFO:获取修正值异常；; URL:%s' % url)
        return False
    del proxy_list[0]
    for proxy in proxy_list:
        try:
            proxy = proxy.find_all('td')
            real_ip = _get_real_value(proxy[0].get_text(), proxy[0]['v'], var_rev)
            real_port = _get_real_value(proxy[1].get_text(), proxy[1]['v'], var_rev, None)
            if real_port == '0000':
                real_port = '8088'
            proxy_iplist.add('%s:%s' % (real_ip, real_port))
        except:
            _logger.exception('STATUS:406 ; INFO:数据解析异常 ; URL:%s' % url)
    # 这家限制只能查看一页
    # subpage = kwargs.get('subpage',False)
    # if not subpage:
    #     page_num = 1
    #     pages = bs.find_all('div',class_ = 'page')
    #     if pages and len(pages) > 1:
    #         page_list = pages[1].find_all('a')
    #         if page_list:
    #             page_num = len(page_list)
    #     if page_num > 1:
    #         #这家站点限制只能查看前3页
    #         if page_num > 3:
    #             page_num = 3
    #         for i in range(2,page_num + 1):
    #             sub_url = '%s&pageid=%s' % (url, i)
    #             res = fetch_proxy_data(sub_url, subpage=True)
    #             res and proxy_iplist.update(res)
    return proxy_iplist


_re_compile_var = None


def _get_var_dict(url, **kwargs):
    '''
    获取解析的变量值
    '''
    global _re_compile_var
    js_url = 'http://ip.zdaye.com/js/base.js'
    if 'headers' not in kwargs:
        kwargs['headers'] = {'referer': url}
    else:
        kwargs['headers']['referer'] = url
    data = fetch(js_url, **kwargs)
    if not data:
        return False
    if _re_compile_var is None:
        _re_compile_var = re.compile('var\s*([\S]+)\s*=\s*\"(\w+)\"\s*;')
    var_list = _re_compile_var.findall(data)
    var_dict = {}
    for var in var_list:
        var_dict[var[0]] = str(var[1])
    return var_dict


def _get_real_value(value, v, key, replace='wait', rev=0):
    '''
    获取真实数值
    :param value:       处理过的值
    :param v:           需要替换的处理值
    :param key:         修正key值
    :param rev:         修正值
    :return:            真实数值
    '''
    vlist = v.split('#')
    ts = ''
    n = len(vlist) - 1
    while n >= 0:
        ts += chr(int(vlist[n]) - key)
        n -= 1
    if not replace:
        value = ts
    else:
        value = value.replace(replace, ts)
    if rev != 0:
        return Util.number_format(value, 0) - rev
    return value


def showm(s):
    '''
    该站点使用的MD5加密（大写）
    :param s:
    :return:
    '''
    return str(hashlib.md5(s).hexdigest()).upper()


def _get_revised_mk(s):
    '''
    获取修正的mk值
    :param s:
    :return:
    '''
    s2 = s.split("m")
    ts = ""
    n = len(s2) - 1
    while n >= 0:
        ts += chr(int(s2[n]) - 352)
        n = n - 1
    return ts


_re_revised_var = None


def _get_revised_var(url, mk, ak, **kwargs):
    '''
    获取修正值

    这家隐蔽性较强
    :return:
    '''
    global _re_revised_var
    _url = 'http://ip.zdaye.com/' + mk + '_' + showm(showm(_get_revised_mk(mk) + 'beiji' + ak)) + '.gif'
    if 'headers' not in kwargs:
        kwargs['headers'] = {'referer': url}
    else:
        kwargs['headers']['referer'] = url
    data = fetch(_url, **kwargs)
    if not data:
        return 0
    return Util.number_format(data, 0)
