# -*- coding: utf-8 -*-
# @Time    : 2019/4/1 10:42
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : app_ssjh.py
# @Software: PyCharm
# @Remarks : 神圣计划app
import hashlib
import json
import logging
import re
import time

from packages import Util, yzwl

session = Util.get_session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G955N Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36 Html5Plus/1.0 (Immersed/25.333334)'
})
db = yzwl.DbSession()
mysql = db.yzwl
_logger = logging.getLogger('yzwl_spider')


lottery_id = {
    '重庆时时彩': 68,
    '天津时时彩': 69,
    '北京PK10': 3,
    '江苏快3': 79,
    '吉林快三': 81,
    '安徽快三': 78,
    '广西快三': 73,
    '北京快三': 84,
    '湖北快三': 74,
    '广东十一选五': 7,
    # '山东十一选五': '',
    '广西十一选五': 112,
    '辽宁十一选五': 53
}
rules = {
    1: ["一星", 1],
    2: ["二星", 2],
    4: ["三星", 3],
    8: ["四星", 4],
    16: ["五星", 5],
    32: ["组三", 6],
    64: ["组六", 7],
    128: ["综合", 8],
    256: ["单双", 9],
    512: ["大小", 10],
    1024: ["三码", 11],
    2048: ["四码", 12],
    4096: ["五码", 13],
    8192: ["六码", 14],
    16384: ["七码", 15],
    32768: ["多码", 16],
    65536: ["胆码", 17],
    131072: ["组选", 18],
    262144: ["龙虎", 19],
    524288: ["多星", 20]
}


def get_sign(key_list):
    md = hashlib.md5()
    u_key = 'fdsajfkljasdfklsdjafkljasdff1421sda3f51sd32f1'
    base_str = u_key + ''.join(key_list)
    md.update(base_str.encode())
    return md.hexdigest().lower()


def save_to_data(item, db_name):
    info = mysql.select(db_name, condition=[('plan_id', item['plan_id']), ('keyword', item['keyword']), ('date', item['date'])], limit=1)
    if not info:
        # 新增
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 计划名:%s;' % (db_name, item['plan_name']))
    else:
        content = info['content']
        if content != item['content']:
            mysql.update(db_name, data=item, condition=[('plan_id', item['plan_id']), ('keyword', item['keyword']), ('date', item['date'])])
            _logger.info('INFO:  DB:%s 数据更新')
        else:
            _logger.info('INFO:  DB:%s 已存在的数据')


def get_data(u_id, u_key, jh_id, cz, jh_flag):
    qi = '0'
    sign = get_sign([u_id, u_key, cz, qi, jh_id, jh_flag])
    url = 'http://www.shenshengjihua.com:8080/shensheng/getdata?cz={}&qi={}&jhid={}&jhflag={}&uid={}&t={}&sign={}'.format(
        cz, qi, jh_id, jh_flag, u_id, u_key, sign)
    r = session.get(url)
    if r.status_code == 200:
        data = r.json()
        time.sleep(2)
        return data


def get_jhid_list(u_id, u_key):
    sign = get_sign([u_id, u_key])
    url = 'http://www.shenshengjihua.com:8080/shensheng/GetJhList?userid={}&t={}&sign={}'.format(u_id, u_key, sign)
    r = session.get(url)
    if r.status_code == 200:
        data = r.json()
        return data.get('lst')


def login(username, password):
    time_stamp = str(time.time())
    sign = get_sign([time_stamp, username, password])
    url = 'http://www.shenshengjihua.com:8080/shensheng/login?' \
          'username={}&password={}&t={}&sign={}'.format(username, password, time_stamp, sign)
    r = session.get(url)
    if r.status_code == 200:
        data = r.json()
        key = data.get('ukey')
        user_id = data.get('id')
        return str(user_id), key


def main():
    username = 'wu6619'
    password = 'wu6619'
    u_id, u_key = login(username, password)
    jh_list = get_jhid_list(u_id, u_key)
    filter_dict = {
        '重庆时时彩': [],
        '天津时时彩': [],
        '北京PK10': [],
    }
    lo_list = ['重庆时时彩', '天津时时彩', '北京PK10', '其它彩种']
    other_list = ['江苏快3', '吉林快三', '安徽快三', '广西快三', '北京快三', '湖北快三', '广东十一选五', '广西十一选五', '辽宁十一选五']
    for jh in jh_list:
        try:
            jh_flag = ''
            jh_id = jh['id']
            jh_name = jh['name']
            jh_rule = jh['rules']
            lo_type = jh['tpname']
            if lo_type in lo_list:
                if lo_type == '其它彩种' and jh_name not in other_list:
                    continue
                elif lo_type != '其它彩种' and jh_rule in filter_dict[lo_type]:
                    continue
                if jh_name == '后二复试A':
                    continue
                if lo_type != '其它彩种':
                    filter_dict[lo_type].append(jh_rule)
                # plan_dict = {
                #     'plan_id': jh_id,
                #     'lottery_id': lottery_id[lo_type] if lo_type != '其它彩种' else lottery_id[jh_name],
                #     'plan_name': jh_name,
                #     'tricks': rules[jh_rule][1],
                # }
                # save_to_data(item=plan_dict, db_name='t_lottery_planid')
                cz_type = jh['type']
                data = get_data(u_id, u_key, str(jh_id), str(cz_type), jh_flag)
                while not data['msgErr']:
                    _logger.error('账号状态出错，重新登录')
                    time.sleep(10)
                    u_id, u_key = login(username, password)
                    data = get_data(u_id, u_key, str(jh_id), str(cz_type), jh_flag)
                content = data['content']
                # jh_flag = data['flag']
                detail_list = content.split('\r\n')
                for d in detail_list:
                    flag = re.findall(r'\d+-\d+ ', d)
                    if flag and '【' in d:
                        key_list = d.split(' ')
                        item = {
                            'plan_id': jh_id,
                            'keyword': key_list[0] + key_list[1].replace('神圣', '云彩').replace('少女', '云彩'),
                            'plan_name': jh_name,
                            'date': time.strftime('%Y-%m-%d', time.localtime()),
                            'content': d.replace('神圣', '云彩').replace('少女', '云彩')
                        }
                        save_to_data(item, 't_lottery_plan')
        except Exception as e:
            _logger.error('error:{}'.format(e))


if __name__ == '__main__':
    main()
