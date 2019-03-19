# -*- coding: utf-8 -*-
# @Time    : 2019/3/18 17:40
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : sfc_aicai.py
# @Software: PyCharm
import json

import requests
import pymysql

from lxml import etree


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


def get_data_from_mysql():
    db = pymysql.connect(host='192.168.2.22', user='root', password='root', database="lottery_info")
    cursor = db.cursor()
    sql = 'SELECT expect, open_result FROM game_sfc_result;'
    cursor.execute(sql)
    data = cursor.fetchall()
    db.close()
    return data


def update_mysql():
    data_dict = get_data()
    db = pymysql.connect(host='192.168.2.22', user='root', password='root', database="lottery_info")
    cursor = db.cursor()
    sql_data = get_data_from_mysql()
    for data in sql_data:
        issue = data[0]
        if data_dict.get(issue):
            open_result = json.loads(data[1])
            for i in range(len(data_dict[issue])):
                if open_result['matchResults'][i]['results'] != '*':
                    open_result['matchResults'][i]['score'] = data_dict[issue][i][2]
            sql = "UPDATE game_sfc_result SET open_result='{}' WHERE expect={}".format(json.dumps(open_result, ensure_ascii=True), issue)
            try:
                cursor.execute(sql)
                db.commit()
            except Exception as e:
                print(e)
                db.rollback()


if __name__ == '__main__':
    update_mysql()
