# -*- coding: utf-8 -*-
# @Time    : 2019/3/28 17:56
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : jsfc.py
# @Software: PyCharm
# @Remarks : 江苏福彩网
import re

from lxml import etree
from packages import Util


session = Util.get_session()


def _parse_detail_data(data, url, **kwargs):
    lo_type = kwargs.get('lo_type')
    if lo_type == 'ssq':
        reds = data.xpath('./table[1]/tbody/tr/td')
        red_num = []
        for red in reds[1:]:
            red_num += red.xpath('./span/strong/text()')[0]
        blue_num = data.xpath('./table[2]/tbody/tr/td[2]/span/strong/text()')[0]
        desc = data.xpath('./p[5]/span/span/text()')
        national_sale, rolling = re.findall(r'投注总额(.*?)元,.*?累计(.*?)元滚入', desc)[0]
        bonus = {
            "rolling": rolling,
            "bonusSituationDtoList": [
                {"winningConditions": "6+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "一等奖"},
                {"winningConditions": "6+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "二等奖"},
                {"winningConditions": "5+1", "numberOfWinners": "0", "singleNoteBonus": "3000", "prize": "三等奖"},
                {"winningConditions": "5+0,4+1", "numberOfWinners": "0", "singleNoteBonus": "200", "prize": "四等奖"},
                {"winningConditions": "4+0,3+1", "numberOfWinners": "0", "singleNoteBonus": "10", "prize": "五等奖"},
                {"winningConditions": "2+1,1+1,0+1", "numberOfWinners": "0", "singleNoteBonus": "5", "prize": "六等奖"}
            ],
            "nationalSales": national_sale,
            "currentAward": "0"
        }
        i = 0
        for bonus in data.xpath('./table[3]/tbody/tr')[1:]:
            prize_num = data.xpath('./td[2]/span/span/strong/text()')[0]
            prize_bonus = data.xpath('./td[3]/span/span/strong/text()')[0]
            bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
            bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
            i += 1
    elif lo_type == 'fc3d':
        code = data.xpath('./table[1]/tbody/tr/td/span/strong/text()')
        desc = data.xpath('./p[5]/span/span/text()')[0]
        national_sale = re.findall('本期投注总额(.*?)元', desc)[0]
        bonus = {
            "rolling": "0", "bonusSituationDtoList": [
                {"winningConditions": "与开奖号相同且顺序一致", "numberOfWinners": "0", "singleNoteBonus": "1040", "prize": "直选"},
                {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": "0", "singleNoteBonus": "346", "prize": "组三"},
                {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": "0", "singleNoteBonus": "173", "prize": "组六"},
            ],
            "nationalSales": national_sale,
            "currentAward": "0"
        }
        i = 0
        for bonus in data.xpath('./table[2]/tbody/tr')[1:]:
            prize_num = data.xpath('./td[2]/span/span/strong/text()')[0]
            prize_bonus = data.xpath('./td[3]/span/span/strong/text()')[0]
            bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
            bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
            i += 1
    elif lo_type == 'qlc':
        code = data.xpath('./table[1]/tbody/tr/td/span/strong/text()')
        desc = data.xpath('./p[6]/span/span/text()')[0]
        national_sale = re.findall('投注总额(.*?)元', desc)[0]
        bonus = {
            "rolling": "0",
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
        for bonus in data.xpath('./table[2]/tbody/tr')[1:]:
            prize_num = data.xpath('./td[2]/span/span/strong/text()')[0]
            prize_bonus = data.xpath('./td[3]/span/span/strong/text()')[0]
            bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
            bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
            i += 1
    elif lo_type == '15x5':
        code = data.xpath('./table[1]/tbody/tr/td/span/strong/text()')
        desc = data.xpath('./p[5]/span/span/text()')[0]
        national_sale, rolling = re.findall(r'投注总额(.*?)元,.*?累计(.*?)元滚入', desc)[0]
        bonus = {
            "rolling": rolling, "bonusSituationDtoList": [
                {"winningConditions": "中5连4", "numberOfWinners": "0", "singleNoteBonus": "1040", "prize": "特别奖"},
                {"winningConditions": "中5", "numberOfWinners": "0", "singleNoteBonus": "346", "prize": "一等奖"},
                {"winningConditions": "中4", "numberOfWinners": "0", "singleNoteBonus": "173", "prize": "二等奖"},
            ],
            "nationalSales": national_sale,
            "currentAward": "0"
        }
        i = 0
        for bonus in data.xpath('./table[2]/tbody/tr')[1:]:
            prize_num = data.xpath('./td[2]/span/span/strong/text()')[0]
            prize_bonus = data.xpath('./td[3]/span/span/strong/text()')[0]
            bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
            bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
            i += 1
    elif lo_type == 'df6+1':
        code = data.xpath('./table[1]/tbody/tr/td/span/strong/text()')
        desc = data.xpath('./p[6]/span/span/text()')[0]
        national_sale, rolling = re.findall(r'投注总额(.*?)元,.*?累计(.*?)元滚入', desc)[0]
        bonus = {
            "rolling": rolling,
            "bonusSituationDtoList": [
                {"winningConditions": "6位基本号码按位相符且生肖码相符", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "一等奖"},
                {"winningConditions": "6位基本号码按位相符", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "二等奖"},
                {"winningConditions": "5位基本号码按位相符且生肖码相符", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "三等奖"},
                {"winningConditions": "5位（含基本号码和生肖码）按位相符", "numberOfWinners": "0", "singleNoteBonus": "200", "prize": "四等奖"},
                {"winningConditions": "4位（含基本号码和生肖码）按位相符", "numberOfWinners": "0", "singleNoteBonus": "50", "prize": "五等奖"},
                {"winningConditions": "3位（含基本号码和生肖码）按位相符，或1位基本号码按位相符且生肖码相符", "numberOfWinners": "0", "singleNoteBonus": "10", "prize": "六等奖"},
            ],
            "nationalSales": national_sale,
            "currentAward": "0"
        }
        i = 0
        for bonus in data.xpath('./table[2]/tbody/tr')[1:]:
            prize_num = data.xpath('./td[2]/span/span/strong/text()')[0]
            prize_bonus = data.xpath('./td[3]/span/span/strong/text()')[0]
            bonus['bonusSituationDtoList'][i]['numberOfWinners'] = prize_num
            bonus['bonusSituationDtoList'][i]['singleNoteBonus'] = prize_bonus
            i += 1


def fetch_data(url, proxy=None, **kwargs):
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        result = selector.xpath('//*[@id="main_content"]/div/div/div/div/table/tbody/tr')
        expect = result[1].xpath('./th/text()')[0]
        data = result[2].xpath('./td')[0]



def main():
    r = session.get('http://www.jslottery.com/')
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        lotterys = selector.xpath('//*[@id="lotterynum"]/table/tbody/tr')
        for lottery in lotterys:
            url = lottery.xpath('./td/table/tbody/tr/td[2]/div[2]/a/@href')
            fetch_data("http://www.jslottery.com" + url[0])
