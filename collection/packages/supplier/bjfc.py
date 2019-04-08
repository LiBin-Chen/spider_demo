# -*- coding: utf-8 -*-
# @Time    : 2019/4/8 14:35
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : bjfc.py
# @Software: PyCharm
# @Remarks : 北京福彩网
import json
import re

from lxml import etree

from packages import Util

session = Util.get_session()


def fetch_data(url, **kwargs):
    lo_type = kwargs.get('lo_type')
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        expect = selector.xpath('//*[@id="lottery_tabs"]/div/text()[1]')
        codes = selector.xpath('//*[@id="lottery_tabs"]/div/table[1]/tbody/tr[2]/td')
        desc = selector.xpath('//*[@id="lottery_tabs"]/div/text()[3]')
        if lo_type == 'ssq':
            num_1 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[2]/td[2]/text()')[0]
            prize_1 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[2]/td[3]/text()')[0]
            num_2 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[3]/td[2]/text()')[0]
            prize_2 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[3]/td[3]/text()')[0]
            num_3 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[4]/td[2]/text()')[0]
            num_4 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[5]/td[2]/text()')[0]
            num_5 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[6]/td[2]/text()')[0]
            num_6 = selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[7]/td[2]/text()')[0]
            national_sale, rolling = re.findall(r'投注总额为 (\d+) 元，奖池金额为 (\d+) 元', desc[0])[0]
            bonus = {
                "rolling": rolling,
                "bonusSituationDtoList": [
                    {"winningConditions": "6+1", "numberOfWinners": num_1, "singleNoteBonus": prize_1, "prize": "一等奖"},
                    {"winningConditions": "6+0", "numberOfWinners": num_2, "singleNoteBonus": prize_2, "prize": "二等奖"},
                    {"winningConditions": "5+1", "numberOfWinners": num_3, "singleNoteBonus": "3000", "prize": "三等奖"},
                    {"winningConditions": "5+0,4+1", "numberOfWinners": num_4, "singleNoteBonus": "200", "prize": "四等奖"},
                    {"winningConditions": "4+0,3+1", "numberOfWinners": num_5, "singleNoteBonus": "10", "prize": "五等奖"},
                    {"winningConditions": "2+1,1+1,0+1", "numberOfWinners": num_6, "singleNoteBonus": "5", "prize": "六等奖"}
                ],
                "nationalSales": national_sale,
                "currentAward": "0"
            }
            i = 0
            for b in selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr')[1:7]:
                prize_num = b.xpath('./td[2]/text()')[0]
                prize_bonus = b.xpath('./td[3]/text()')[0]
                bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
                bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
                i += 1
        elif lo_type == '3d':
            national_sale, current_award = re.findall(r'本期投注总额为 (\d+) 元，中奖总金额为 (\d+) 元', desc)[0]
            bonus = {
                "rolling": '0',
                "bonusSituationDtoList": [
                    {"winningConditions": "与开奖号相同且顺序一致",
                     "numberOfWinners": selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[2]/td[2]')[0],
                     "singleNoteBonus": "1040", "prize": "直选"},
                    {"winningConditions": "与开奖号相同，顺序不限",
                     "numberOfWinners": selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[3]/td[2]')[0],
                     "singleNoteBonus": "346", "prize": "组三"},
                    {"winningConditions": "与开奖号相同，顺序不限",
                     "numberOfWinners": selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr[4]/td[2]')[0],
                     "singleNoteBonus": "173", "prize": "组六"},
                ],
                "nationalSales": national_sale,
                "currentAward": current_award
            }
        else:
            national_sale, rolling = re.findall(r'本期投注总额为 (\d+) 元，奖池金额为 (\d+) 元', desc)[0]
            bonus = {
                "rolling": rolling,
                "bonusSituationDtoList": [
                    {"winningConditions": "7+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "一等奖"},
                    {"winningConditions": "6+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "二等奖"},
                    {"winningConditions": "6+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "三等奖"},
                    {"winningConditions": "5+1", "numberOfWinners": "0", "singleNoteBonus": "200", "prize": "四等奖"},
                    {"winningConditions": "5+0", "numberOfWinners": "0", "singleNoteBonus": "50", "prize": "五等奖"},
                    {"winningConditions": "4+1", "numberOfWinners": "0", "singleNoteBonus": "10", "prize": "六等奖"},
                    {"winningConditions": "4+0", "numberOfWinners": "0", "singleNoteBonus": "5", "prize": "七等奖"},
                ],
                "nationalSales": national_sale,
                "currentAward": "0"
            }
            i = 0
            for b in selector.xpath('//*[@id="lottery_tabs"]/div/table[2]/tbody/tr')[1:8]:
                prize_num = b.xpath('./td[2]/text()')[0]
                prize_bonus = b.xpath('./td[3]/text()')[0]
                bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
                bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
                i += 1
        item = {
            'expect': expect[0].replace('第', '').replace('期', ''),
            'cp_id': '',
            'cp_sn': '22' + expect,
            'open_time': '',
            'open_code': '',
            'open_date': '',
            'open_detail_url': url,
            'open_result': json.dumps(bonus)
        }


def main():
    lo_dict = {
        'ssq': 'slto',
        '3d': 'pk3',
        'qlc': 'loto'
    }
    for key, value in lo_dict.items():
        url = 'http://www.bwlc.net/bulletin/{}.html'.format(value)
        fetch_data(url)


if __name__ == '__main__':
    pass
