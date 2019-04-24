# -*- coding: utf-8 -*-
# @Time    : 2019/4/24 10:48
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_espn.py
# @Software: PyCharm
# @Remarks : 体育信息

from lxml import etree
from packages import Util


session = Util.get_session('http://global.espn.com/')


def get_events():
    url = 'http://global.espn.com/football/competitions'
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        events = selector.xpath('//*[@class="layout is-split"]/div/section/section/div/section')


def fetch_base_message():
    pass
