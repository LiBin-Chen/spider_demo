# -*- coding: utf-8 -*-
# @Time    : 2019/3/19 11:25
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_aicai_sfc.py
# @Software: PyCharm
# @Remarks : 新浪爱彩胜负彩获取最新一期数据
import json

import pymysql
import requests
from lxml import etree

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
})


def get_data():
    url = 'https://kaijiang.aicai.com/sfc/'
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        issue = selector.xpath('//*[@id="jq_last10_issue_no"]/option[1]/text()')[0]
        session.headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        data_url = 'https://kaijiang.aicai.com/open/historyIssue.do'
        post_data = {
            'gameIndex': 401,
            'issueNo': issue
        }
        r = session.post(url, post_data)
        if r.status_code == 200:
            data = json.loads(r.content.decode('utf8'))
            if data['raceHtml']:
                s = etree.HTML(data['raceHtml'])
                results = s.xpath('//tr')
