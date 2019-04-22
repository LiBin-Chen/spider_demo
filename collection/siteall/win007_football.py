# -*- coding: utf-8 -*-
# @Time    : 2019/4/10 15:24
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : win007_football.py
# @Software: PyCharm
# @Remarks : 球探网足球信息
import os
import re
import sys
import time
import logging
cur_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(cur_dir))
from packages import Util, yzwl

session = Util.get_session('http://zq.win007.com/info/index_cn.htm')
db = yzwl.DbClass(db_name='sports_data_center_bak')
mysql = db.yzwl
_logger = logging.getLogger('yzwl_spider')


def save_data(item, db_name):
    info = mysql.select(db_name, condition=[('id', '=', item['id'])])
    if not info:
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 比赛id %s ;' % (db_name, item['id']))
    else:
        mysql.update(db_name, data=item, condition=[('id', '=', item['id'])])
        _logger.info('INFO:  DB:%s 数据已存在, 更新成功, 比赛id %s ;' % (db_name, item['id']))


def get_football_match():
    football_url = []
    url = 'http://zq.win007.com/jsData/infoHeader.js'
    session.headers.update({
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Host': 'zq.win007.com',
        'Referer': 'http://zq.win007.com/info/index_cn.htm',
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
                    if data[3] == '0':
                        match_type = 'League'
                    elif data[3] == '1':
                        match_type = 'SubLeague'
                if data[2] == '2':
                    match_type = 'CupMatch'
                if match_type:
                    # 如要最新的，取data[4:5],如要历史的 取data[4:]
                    for year in data[4:5]:
                        info_url = 'http://zq.win007.com/cn/{}/{}/{}.html'.format(match_type, year, match_id)
                        url_list.append(info_url)
                football_url.append(url_list)
    return football_url


def _parse_detail_data(data, team_dict, round_num):
    try:
        match_id = data[0]
        event_id = data[1]
        match_date = data[3]
        match_time_stamp = int(time.mktime(time.strptime(match_date, '%Y-%m-%d %H:%M')))
        host_team_id = data[4]
        host_name = team_dict[host_team_id][0]
        host_logo = team_dict[host_team_id][1]
        guest_team_id = data[5]
        guest_name = team_dict[guest_team_id][0]
        guest_logo = team_dict[guest_team_id][1]
        score = data[6].split('-') if data[6] else ['NULL', 'NULL']
        if len(score) == 1:
            return
        half_score = data[7].split('-') if data[7] else ['NULL', 'NULL']
        host_rank = data[8]
        guest_rank = data[9]
        host_red = data[18]
        guest_red = data[19]
        item = {
            'id': match_id,
            'event_id': event_id,
            'status': 8 if score[0] != 'NULL' else 1,
            'match_time': match_time_stamp,
            'open_time': match_time_stamp,
            'rounds': round_num,
            'host_name_zh': host_name,
            'host_id': host_team_id,
            'host_ranking': host_rank,
            'host_logo': host_logo,
            'guest_name_zh': guest_name,
            'guest_id': guest_team_id,
            'guest_ranking': guest_rank,
            'guest_logo': guest_logo,
            'host_red': host_red,
            'guest_red': guest_red
        }
        if score[0] and score[0] != 'NULL':
            item['host_score'] = score[0]
        if score[1] and score[1] != 'NULL':
            item['guest_score'] = score[1]
        if half_score[0] and half_score[0] != 'NULL':
            item['host_half_score'] = half_score[0]
        if half_score[1] and half_score[1] != 'NULL':
            item['guest_half_score'] = half_score[1]
        save_data(item, 't_football_match')
    except Exception as e:
        print("error:" + str(e))


def fetch_data(url, mark=0):
    """

    :param url:
    :param mark: 是否只获取一条数据的标记
    :return:
    """
    try:
        session.headers.update({
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        for i in range(3):
            try:
                r = session.get(url)
                time.sleep(0.5)
                break
            except Exception as e:
                print('request retry ' + str(i + 1))
        if r.status_code == 200:
            js_data = r.content.decode('utf8')
            arr_team = re.findall(r'arrTeam = (\[.*]);', js_data)
            team_list = eval(arr_team[0])
            team_dict = {}
            for team in team_list:
                team_id = team[0]
                team_zh_name = team[1]
                team_logo = 'http://zq.win007.com/Image/team/' + team[5] if len(team) > 5 else 'NULL'
                team_dict[team_id] = [team_zh_name, team_logo]
            arr_subleague = re.findall(r'var arrSubLeague = (\[.*]);', js_data)
            league_data = re.findall(r'var arrLeague = (\[.*]);', js_data)
            cup_data = re.findall(r'var arrCup = (\[.*]);', js_data)
            if league_data:
                event_data = eval(league_data[0])
                print(event_data[1] + event_data[4] + event_data[-4])
                if arr_subleague and mark == 0:
                    league_list = eval(arr_subleague[0])
                    if len(league_list) > 1:
                        for i in league_list:
                            new_url = re.sub(re.compile(r'_(\d+)\.js\?'), '_{}.js?'.format(str(i[0])), url)
                            fetch_data(new_url, mark=1)
                        return
                round_info = re.findall(r'jh\["R_(\d+)"] = (\[.*?]);', js_data)

                for match_round in round_info:
                    round_num = int(match_round[0])
                    round_data = eval(match_round[1].replace(',,,', ",'NULL','NULL',").replace(',,', ",'NULL',"))
                    if round_data:
                        for rd in round_data:
                            try:
                                if len(rd) < 20:
                                    for m in rd[4:]:
                                        _parse_detail_data(m, team_dict, round_num)
                                    continue
                                _parse_detail_data(rd, team_dict, round_num)
                            except Exception as e:
                                print("error:" + str(e))
            elif cup_data:
                event_data = eval(cup_data[0])
                print(event_data[1] + event_data[4] + event_data[-4])
                match_info = re.findall(r'jh\["G\d+[A-Z]?"] = (\[.*?]);', js_data)
                for match_round in match_info:
                    match_data = eval(match_round.replace(',,,', ",'NULL','NULL',").replace(',,', ",'NULL',"))
                    if match_data:
                        for md in match_data:
                            try:
                                if len(md) < 20:
                                    for m in md[4:]:
                                        _parse_detail_data(m, team_dict, 0)
                                    continue
                                _parse_detail_data(md, team_dict, 0)
                            except Exception as e:
                                print("error:" + str(e))

    except Exception as e:
        print(e)


def main():
    url_list = get_football_match()
    for league_list in url_list:
        for url in league_list:
            r = session.get(url)
            if r.status_code == 200:
                html = r.content.decode('utf8')
                js_src = re.findall(r'src="(/jsData/matchResult/.*?)">', html)
                if js_src:
                    js_url = 'http://zq.win007.com' + js_src[0]
                    fetch_data(js_url)


if __name__ == '__main__':
    main()
