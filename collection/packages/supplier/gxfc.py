# -*- coding: utf-8 -*-
# @Time    : 2019/3/29 15:40
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : gxfc.py
# @Software: PyCharm
# @Remarks : 广西福彩
import json
import time

from lxml import etree
from packages import Util


session = Util.get_session('http://www.gxcaipiao.com.cn/')


def _parse_detail_data(data, url, **kwargs):
    lott_name = data.xpath('./@lottname')[0]
    expect = data.xpath('./@perdid')[0]
    code = data.xpath('./@awardcode')[0].replace('|', '+')
    open_date = data.xpath('./@awarddate')[0]
    global_sale = data.xpath('./@globalsale')[0]
    rolling = data.xpath('./pools/pool/@money')[0]
    level = data.xpath('./levels/level')
    if lott_name == '双色球':
        bonus = {
            "rolling": rolling,
            "bonusSituationDtoList": [
                {"winningConditions": "6+1", "numberOfWinners": level[0].xpath('./@globalcount')[0], "singleNoteBonus": level[0].xpath('./@money')[0], "prize": "一等奖"},
                {"winningConditions": "6+0", "numberOfWinners": level[1].xpath('./@globalcount')[0], "singleNoteBonus": level[1].xpath('./@money')[0], "prize": "二等奖"},
                {"winningConditions": "5+1", "numberOfWinners": level[2].xpath('./@globalcount')[0], "singleNoteBonus": "3000", "prize": "三等奖"},
                {"winningConditions": "5+0,4+1", "numberOfWinners": level[3].xpath('./@globalcount')[0], "singleNoteBonus": "200", "prize": "四等奖"},
                {"winningConditions": "4+0,3+1", "numberOfWinners": level[4].xpath('./@globalcount')[0], "singleNoteBonus": "10", "prize": "五等奖"},
                {"winningConditions": "2+1,1+1,0+1", "numberOfWinners": level[5].xpath('./@globalcount')[0], "singleNoteBonus": "5", "prize": "六等奖"}
            ],
            "nationalSales": global_sale,
            "currentAward": "0"
        }
    elif lott_name == '七乐彩':
        bonus = {
            "rolling": rolling,
            "bonusSituationDtoList": [
                {"winningConditions": "7+0", "numberOfWinners": level[0].xpath('./@globalcount')[0], "singleNoteBonus": level[0].xpath('./@money')[0], "prize": "一等奖"},
                {"winningConditions": "6+1", "numberOfWinners": level[1].xpath('./@globalcount')[0], "singleNoteBonus": level[1].xpath('./@money')[0], "prize": "二等奖"},
                {"winningConditions": "6+0", "numberOfWinners": level[2].xpath('./@globalcount')[0], "singleNoteBonus": level[2].xpath('./@money')[0], "prize": "三等奖"},
                {"winningConditions": "5+1", "numberOfWinners": level[3].xpath('./@globalcount')[0], "singleNoteBonus": "200", "prize": "四等奖"},
                {"winningConditions": "5+0", "numberOfWinners": level[4].xpath('./@globalcount')[0], "singleNoteBonus": "50", "prize": "五等奖"},
                {"winningConditions": "4+1", "numberOfWinners": level[5].xpath('./@globalcount')[0], "singleNoteBonus": "10", "prize": "六等奖"},
                {"winningConditions": "4+0", "numberOfWinners": level[6].xpath('./@globalcount')[0], "singleNoteBonus": "5", "prize": "七等奖"},
            ],
            "nationalSales": global_sale,
            "currentAward": "0"
        }
    elif lott_name == '3D':
        bonus = {
            "rolling": rolling,
            "bonusSituationDtoList": [
                {"winningConditions": "与开奖号相同且顺序一致", "numberOfWinners": level[0].xpath('./@globalcount')[0], "singleNoteBonus": "1040", "prize": "直选"},
                {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": level[1].xpath('./@globalcount')[0], "singleNoteBonus": "346", "prize": "组三"},
                {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": level[2].xpath('./@globalcount')[0], "singleNoteBonus": "173", "prize": "组六"},
            ],
            "nationalSales": global_sale,
            "currentAward": "0"
        }
    else:
        bonus = {}
    item = {
        'expect': expect,
        'cp_id': code.replace(',', '').replace('+', ''),
        'cp_sn': '20' + expect,
        'open_time': open_date,
        'open_code': code,
        'open_date': open_date[:10],
        'open_detail_url': url,
        'open_result': json.dumps(bonus)
    }


def fetch_data(url, proxy=None, **kwargs):
    index_url = 'http://www.gxcaipiao.com.cn/notice/notice_{}.html'.format(kwargs.get('id'))
    session.headers.update({
        'Accept': 'application/xml, text/xml, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': index_url,
        'X-Requested-With': 'XMLHttpRequest'
    })
    r = session.get(url)
    if r.status_code == 200:
        content = r.content
        selector = etree.HTML(content)
        data = selector.xpath('//lottery[1]')
        _parse_detail_data(data[0], url)


def main(**kwargs):
    lottery = {
        'ssq': '01',
        'qlc': '07',
        'fc3d': '05',
        'klsc': '12'
    }
    for key, value in lottery.items():
        time_stamp = int(time.time()*1000)
        url = 'http://www.gxcaipiao.com.cn/xml/notice_less_{}.xml?timestamp={}'.format(value, time_stamp)
        kwargs['id'] = value
        fetch_data(url, **kwargs)


if __name__ == '__main__':
    main()
