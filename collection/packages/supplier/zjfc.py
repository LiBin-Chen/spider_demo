# -*- coding: utf-8 -*-
# @Time    : 2019/4/3 10:29
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : zjfc.py
# @Software: PyCharm
# @Remarks : 浙江福彩网
import re

from lxml import etree
from packages import Util


session = Util.get_session('http://www.zjflcp.com/')


def api_get_data(url, proxy=None, **kwargs):
    lo_type = kwargs.get('lo_type')
    r = session.get(url)
    content = r.content.decode('utf8')
    selector = etree.HTML(content)
    if lo_type == 'ssq_d':
        expect = selector.xpath('/html/body/div[1]/div/div[2]/div[2]/div/span')
        cp_sn = '21' + expect
        date = selector.xpath('/html/body/div[1]/div/div[2]/div[3]/text()')
        open_date = re.findall(r'\d{4}-\d{2}-\d{2}', date[0])[0]
        open_time = open_date + ' 21:15:00'
        codes = selector.xpath('/html/body/div[1]/div/div[2]/ul[1]/li/text()')
        open_code = ','.join(codes[:6]) + '+' + codes[6]
        cp_id = ''.join(codes)
        reward = selector.xpath('/html/body/div[1]/div/div[4]/ul[2]/li')
        total_sale = selector.xpath('/html/body/div[1]/div/div[5]/div[1]/span[1]/text()')
        rolling = selector.xpath('/html/body/div[1]/div/div[5]/div[1]/span[2]')
        open_result = {"rolling": rolling[0], "bonusSituationDtoList": [
            {"winningConditions": "6+1", "numberOfWinners": reward[3].xpath('./text()')[0], "singleNoteBonus": reward[4].xpath('./text()')[0].replace('元/注', ''), "prize": "一等奖"},
            {"winningConditions": "6+0", "numberOfWinners": reward[7].xpath('./text()')[0], "singleNoteBonus": reward[3].xpath('./text()')[0].replace('元/注', ''), "prize": "二等奖"},
            {"winningConditions": "5+1", "numberOfWinners": reward[11].xpath('./text()')[0], "singleNoteBonus": "3000", "prize": "三等奖"},
            {"winningConditions": "5+0,4+1", "numberOfWinners": reward[15].xpath('./text()')[0], "singleNoteBonus": "200", "prize": "四等奖"},
            {"winningConditions": "4+0,3+1", "numberOfWinners": reward[19].xpath('./text()')[0], "singleNoteBonus": "10", "prize": "五等奖"},
            {"winningConditions": "2+1,1+1,0+1", "numberOfWinners": reward[23].xpath('./text()')[0], "singleNoteBonus": "5", "prize": "六等奖"}
        ], "nationalSales": total_sale[0], "currentAward": "0"}
    elif lo_type == 'new_sd_d':
        expect = selector.xpath('//*[@id="zyselect"]/@defaultvalue')
        cp_sn = '21' + expect
        date = selector.xpath('/html/body/div[1]/div/div[2]/div[3]/text()')
        open_date = re.findall(r'\d{4}-\d{2}-\d{2}', date[0])[0]
        open_time = open_date + ' 21:15:00'
        codes = selector.xpath('/html/body/div[1]/div/div[2]/ul[1]/li/text()')
        open_code = ','.join(codes)
        cp_id = ''.join(codes)
        reward = selector.xpath('/html/body/div[1]/div/div[4]/ul[2]/li')
        total_sale = selector.xpath('/html/body/div[1]/div/div[5]/div[1]/span/text()')
        open_result = {"rolling": "0", "bonusSituationDtoList": [
            {"winningConditions": "与开奖号相同且顺序一致", "numberOfWinners": reward[1].xpath('./text()')[0], "singleNoteBonus": "1040", "prize": "直选"},
            {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": reward[4].xpath('./text()')[0], "singleNoteBonus": "346", "prize": "组三"},
            {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": reward[7].xpath('./text()')[0], "singleNoteBonus": "173", "prize": "组六"},
        ], "nationalSales": total_sale[0], "currentAward": "0"}
    else:
        data = selector.xpath('/html/body/table/tbody/tr/td/table[1]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr[3]/td/table[2]/tbody/tr')
        newest = data[1]
        date = newest.xpath('./td[1]/a/text()')
        expect = newest.xpath('./td[2]/text()')
        cp_sn = '21' + expect
        code = newest.xpath('./td[3]/text()')
        open_code = code[0].replace(' ', '')
        cp_id = open_code.replace(',', '').replace('+', '')


def main():
    lottery_list = ['ssq_d', 'new_sd_d', 'qlc', 'swxw']
    for lottery in lottery_list:
        url = 'http://zjflcp.zjol.com.cn/fcweb/{}.html'.format(lottery)
