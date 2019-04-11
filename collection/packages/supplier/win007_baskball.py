# -*- coding: utf-8 -*-
# @Time    : 2019/4/10 16:12
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : win007_baskball.py
# @Software: PyCharm
# @Remarks :
import random
import re
import time
import logging
from packages import Util, yzwl

db = yzwl.DbClass(db_name='sports_data_center_bak')
mysql = db.yzwl
_logger = logging.getLogger('yzwl_spider')


session = Util.get_session('http://nba.win007.com/index_cn.htm')


def save_to_db(item, db_name):
    info = mysql.select(db_name, condition=[('match_id', '=', item['match_id'])])
    if not info:
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 比赛id %s ;' % (db_name, item['match_id']))
    else:
        mysql.update(db_name, data=item, condition=[('match_id', '=', item['match_id'])])
        _logger.info('INFO:  DB:%s 数据已存在, 更新成功, 比赛id %s ;' % (db_name, item['match_id']))


def get_basketball_match():
    basketball_url = []
    url = 'http://nba.win007.com/jsData/infoHeader_cn.js'
    session.headers.update({
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    })
    r = session.get(url)
    if r.status_code == 200:
        source_data = r.content.decode('utf8')
        matches = re.findall(r'arr\[\d+] = (\[.*?]);', source_data)
        for match in matches:
            match_list = eval(match)
            infos = match_list[4]
            for info in infos:
                data = info.split(',')
                match_id = data[0]
                url_list = []
                match_type = ''
                if data[2] == '1':
                    match_type = 'Normal'
                elif data[2] == '2':
                    match_type = 'CupMatch'
                if match_type:
                    # 最新取data[3:4], 历史取data[3:]
                    for year in data[3:4]:
                        info_url = 'http://nba.win007.com/cn/{}.aspx?SclassID={}&matchSeason={}'.format(
                            match_type, match_id, year)
                        url_list.append(info_url)
                basketball_url.append(url_list)
    return basketball_url


def parse_data(data, team_dict, event_id):
    match_id = data[0]
    match_time = int(time.mktime(time.strptime(data[2], '%Y-%m-%d %H:%M')))
    host_name = team_dict[data[3]]
    guest_name = team_dict[data[4]]
    host_score = data[5]
    guest_score = data[6]
    host_score_half = data[7]
    guest_score_half = data[8]
    item = {
        'match_id': match_id,
        'event_id': event_id,
        'match_time': match_time,
        'home_id': data[3],
        'home_name': host_name,
        'away_id': data[4],
        'away_name': guest_name,
    }
    if host_score and host_score != 'NULL':
        item['home_fourth_score'] = host_score
    if guest_score and guest_score != 'NULL':
        item['away_fourth_score'] = guest_score
    if host_score_half:
        item['home_second_score'] = host_score_half
    if guest_score_half:
        item['away_second_score'] = guest_score_half
    save_to_db(item, 't_basketball_match')


def get_info(url, mark=0):
    try:
        session.headers.update({
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"
        })
        r = session.get(url)
        if r.status_code == 200:
            time.sleep(0.5)
            js_data = r.content.decode('utf8')
            if js_data:
                arr_league = re.findall(r'var arrLeague = (\[.*]);', js_data)
                league_info = eval(arr_league[0])

                arr_team = re.findall(r'var arrTeam = (\[.*]);', js_data)
                team_list = eval(arr_team[0])
                team_dict = {}
                for team in team_list:
                    team_id = team[0]
                    team_zh_name = team[1]
                    team_dict[team_id] = team_zh_name

                event_id = league_info[0]
                league_name = league_info[1]
                print(league_name)
                if league_info[-1] == 2:
                    match_data = []
                    group_list = re.findall(r'jh\["G\d+[^"]*?"] = (\[.*]);', js_data)
                    for group in group_list:
                        match_data += eval(group.replace(',,,', ",'NULL','NULL',").replace(',,', ",'NULL',"))
                    all_match_list = re.findall(r'jh\["Q\d+"] = (\[.*]);', js_data)
                    for m in all_match_list:
                        match_data += eval(m.replace(',,,', ",'NULL','NULL',").replace(',,', ",'NULL',"))
                    for match in match_data:
                        try:
                            if len(match) != 14:
                                for m in match[4]:
                                    parse_data(m, team_dict, event_id)
                                continue
                            parse_data(match, team_dict, event_id)
                        except Exception as e:
                            print(e)

                elif league_info[-2] == 1:
                    league_type = list(league_info[-1])
                    if len(league_type) > 1 and mark == 0:
                        ym_list = re.findall(r'var ymList = (\[.*]);', js_data)
                        for ym in eval(ym_list[0]):
                            new_url = re.sub(re.compile(r'_\d{4}_\d\.js\?'),
                                             '_{}_{}.js?'.format(str(ym[0]), str(ym[1])), url)
                            get_info(new_url, mark=1)
                        return
                    arr_data = re.findall(r'var arrData = (\[.*]);', js_data)
                    match_info = eval(arr_data[0].replace(',,,', ",'NULL','NULL',").replace(',,', ",'NULL',"))
                    for match in match_info:
                        try:
                            if len(match) != 14:
                                for m in match[4]:
                                    parse_data(m, team_dict, event_id)
                                continue
                            parse_data(match, team_dict, event_id)
                        except Exception as e:
                            print(e)
    except Exception as e:
        print(e)


def main():
    # 使用代理。（目前代理不可用）
    # proxy_num, proxy_list = Util.get_prolist()
    # i = random.randint(0, proxy_num - 1)
    # session.proxies.update({
    #     'http': 'http://' + proxy_list[i],
    #     'https': 'https://' + proxy_list[i]
    # })
    url_list = get_basketball_match()
    for league_url in url_list:
        for url in league_url:
            try:
                r = session.get(url)
                if r.status_code == 200:
                    time.sleep(0.5)
                    html = r.content.decode('utf8')
                    js_src = re.findall(r'src="(/jsData/matchResult/.*?)">', html)
                    if js_src:
                        js_url = 'http://nba.win007.com' + js_src[0]
                        get_info(js_url)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    main()
