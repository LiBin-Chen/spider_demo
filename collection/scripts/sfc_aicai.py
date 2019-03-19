# -*- coding: utf-8 -*-
# @Time    : 2019/3/18 17:40
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : sfc_aicai.py
# @Software: PyCharm
import json
import logging

import requests
import pymysql

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
        issues = selector.xpath('//*[@id="jq_last10_issue_no"]/option/text()')
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
                    s = etree.HTML(data['raceHtml'])
                    results = s.xpath('//tr')
                    match_list = []
                    for result in results:
                        host_team = result.xpath('./td[2]/i[1]/text()')[0]
                        score = result.xpath('./td[2]/i[2]/text()')[0]
                        away_team = result.xpath('./td[2]/i[3]/text()')[0]
                        match_list.append([host_team, away_team, score])
                    result_dict[issue] = match_list
    return result_dict


def save_data(expect, db_name, dlist):
    '''
    有则更新 无则插入
    :param key:
    :param db_name:
    :param item:
    :return:
    '''
    info = mysql.select(db_name, fields=('open_result',), condition=[('expect', '=', expect)], limit=1)
    if not info:
        #新增
        # mysql.insert(db_name, data=item)
        # _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ;' % (db_name, item['expect'], ))
        pass
    else:
        open_result = json.loads(info.get('open_result'), encoding='utf-8')
        matchResults = open_result['matchResults']
        for i in range(len(matchResults)):
            matchResults[i]['homeTeamView'] = dlist[i][0]
            matchResults[i]['awayTeamView'] = dlist[i][1]
            matchResults[i]['score'] = dlist[i][2]
        info['open_result'] = json.dumps(open_result, ensure_ascii=True)
        mysql.update(db_name, condition=[('expect', '=', expect)], data=info)
        _logger.info('INFO:  DB:%s 数据已存在 更新成功, 期号: %s ; ' % (db_name, expect))


def main():
    data_dict = get_data()
    for expect in data_dict:
        dlist = data_dict[expect]
        try:
            save_data(expect, 'game_sfc_result', dlist)
        except Exception as e:
            _logger.exception('mysql异常： %s' % util.traceback_info(e))




if __name__ == '__main__':
    main()
