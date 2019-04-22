# -*- coding: utf-8 -*-
# @Time    : 2019/3/18 17:40
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : sfc_aicai.py
# @Software: PyCharm
import json
import logging
import time

import requests

from lxml import etree
from packages import yzwl
from packages import Util as util

db = yzwl.DbSession()
mysql = db.yzwl

_logger = logging.getLogger('yzwl_spider')


def get_data():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
    })
    r = session.get('https://kaijiang.aicai.com/sfc/')
    result_dict = {}
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        issues = selector.xpath('//*[@id="jq_last10_issue_no"]/option[1]/text()')
        session.headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        for issue in issues:
            url = 'https://kaijiang.aicai.com/open/historyIssue.do'
            post_data = {
                'gameIndex': 401,
                'issueNo': issue
            }
            r = session.post(url, post_data)
            if r.status_code == 200:
                data = json.loads(r.content.decode('utf8'))
                if data['raceHtml']:
                    prize_1_num = int(data['count1'].replace(',', ''))
                    prize_1 = int(data['prize1'].replace(',', ''))
                    prize_2_num = int(data['count2'].replace(',', ''))
                    prize_2 = int(data['prize2'].replace(',', ''))
                    cp_id = data['openResult'].replace('<i>', '').replace('</i>', '')
                    open_code = ','.join(list(cp_id))
                    cp_sn = '17' + issue
                    sale_value = int(data['saleValue'].replace(',', ''))
                    prize_pool = int(data['prizePool'].replace(',', ''))
                    open_time = str(time.gmtime().tm_year) + '-' + data['openTime'] + ' 10:00:00'
                    time_t = time.strptime(open_time, '%Y-%m-%d %H:%M:%S')
                    s = etree.HTML(data['raceHtml'])
                    results = s.xpath('//tr')
                    match_list = []
                    data_item = {"rolling": prize_pool,
                                 "nationalSales": sale_value,
                                 "currentAward": prize_1_num * prize_1 + prize_2_num * prize_2,
                                 "bonusSituationDtoList": [
                                            {"numberOfWinners": prize_1_num,
                                             "singleNoteBonus": prize_1,
                                             "additionNumber": "0",
                                             "additionBonus": "0",
                                             "winningConditions": "14场比赛的胜平负结果全中",
                                             "prize": "一等奖"},
                                            {"numberOfWinners": prize_2_num,
                                             "singleNoteBonus": prize_2,
                                             "additionNumber": "0",
                                             "additionBonus": "0",
                                             "winningConditions": "13场比赛的胜平负结果全中",
                                             "prize": "二等奖"}],
                                 'matchResults': [],
                                 }
                    for result in results:
                        host_team = result.xpath('./td[2]/i[1]/text()')[0]
                        score = result.xpath('./td[2]/i[2]/text()')[0]
                        away_team = result.xpath('./td[2]/i[3]/text()')[0]
                        match_result = result.xpath('./td[3]/text()')[0]
                        data_item['matchResults'].append({
                            "awayTeamView": away_team,
                            "homeTeamView": host_team,
                            "results": match_result,
                            "score": score
                        })
                    result_dict[issue] = match_list
                    item = {
                        'cp_id': cp_id,
                        'cp_sn': cp_sn,
                        'expect': issue,
                        'open_time': open_time,
                        'open_code': open_code,
                        'open_date': time.strftime('%Y{}%m{}%d{} %H:%M', time_t).format('年', '月', '日'),
                        'open_url': url,
                        'open_details_url': '',
                        'open_video_url': '',
                        'open_content': '',
                        'open_result': json.dumps(data_item, ensure_ascii=True),
                        'create_time': util.date()
                    }
                    save_data(issue, 'game_sfc_result', item)


def save_data(expect, db_name, item):
    """
    有则更新 无则插入
    :param item:
    :param expect:
    :param db_name:
    :return:
    """
    info = mysql.select(db_name, fields=('open_result',), condition=[('expect', '=', expect)], limit=1)
    if not info:
        # 新增
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ;' % (db_name, item['expect'], ))
    else:
        open_result = json.loads(info.get('open_result'), encoding='utf-8')
        matchResults = open_result['matchResults']
        for i in range(len(matchResults)):
            matchResults[i] = json.loads(item['open_result'])['matchResults'][i]
        info['open_result'] = json.dumps(open_result, ensure_ascii=True)
        mysql.update(db_name, condition=[('expect', '=', expect)], data=info)
        _logger.info('INFO:  DB:%s 数据已存在 更新成功, 期号: %s ; ' % (db_name, expect))


if __name__ == '__main__':
    get_data()
