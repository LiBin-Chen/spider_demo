# -*- coding: utf-8 -*-
import requests

import requests
from lxml import etree

__author__ = 'snow'
__time__ = '2019/3/10'
default_headers = {
    'Host': 'kaijiang.500.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
}


def get_dlt():
    rs = requests.get('http://kaijiang.500.com/dlt.shtml', headers=default_headers)
    rs.encoding = rs.apparent_encoding
    # print(rs.text)
    root = etree.HTML(rs.text)
    dlt_expect = root.xpath('//div[@class="iSelectList"]//a//text()')
    return dlt_expect


def get_expect(url):
    if not url:
        print('请输入有效的url')
        return
    rs = requests.get(url=url, headers=default_headers)
    rs.encoding = rs.apparent_encoding
    # print(rs.text)
    root = etree.HTML(rs.text)
    dlt_expect = root.xpath('//div[@class="iSelectList"]//a//text()')
    return dlt_expect


def get_gov_expexc(url, f=None):
    if f:
        with open(url, 'r') as fp:
            content = fp.readlines()
            dlt_expect = [vo.strip('\n') for vo in content]
    else:
        _header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'Hm_lvt_8929ffae85e1c07a7ded061329fbf441=1552747216,1552766134,1552795581,1552801656; Hm_lpvt_8929ffae85e1c07a7ded061329fbf441=1552801656; JSESSIONID=DD2F72D3F13026DECABD380A61FC5887',
            'Host': 'www.lottery.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
        }
        if not url:
            print('请输入有效的url')
            return
        rs = requests.get(url=url, headers=_header)
        rs.encoding = rs.apparent_encoding
        # print(rs.text)
        root = etree.HTML(rs.text)
        dlt_expect = root.xpath('//div[@class="result"]//tr//td[1]//text()')
    return dlt_expect
