# -*- coding: utf-8 -*-
# @Time    : 2019/4/9 15:45
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_cpyzj_gp.py
# @Software: PyCharm
# @Remarks : 彩票易中奖高频彩采集
import os
import sys
import time
import execjs
import logging
cur_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(cur_dir))
from packages import Util, yzwl

session = Util.get_session()
db = yzwl.DbClass()
mysql = db.yzwl
test_mysql = db.test_yzwl
_logger = logging.getLogger('yzwl_spider')


def save_data(url, db_name, item):
    info = mysql.select(db_name, condition=[('expect', '=', item['expect'])], limit=1)
    if not info:
        mysql.insert(db_name, data=item)
        test_mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ; URL:%s' % (db_name, item['expect'], url))
    else:
        # mysql.update(db_name, condition=[('expect', '=', item['expect'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在, 期号: %s' % (db_name, item['expect']))


def get_sign(key):
    """
        直接调用js加密获取sign值
    :param key: 需要加密的字段
    :return: sign
    """
    with open('../scripts/md5.js') as f:
        js_data = f.read()
    ctx = execjs.compile(js_data)
    sign = ctx.call('md5', key)
    return sign


def get_open_data(url, post_data):
    try:
        r = session.post(url, post_data)
        if r.status_code == 200:
            data = r.json()
            return data
    except Exception as e:
        _logger.error('request error: %s' % Util.traceback_info(e))


def get_newest_data(url, **kwargs):
    lot_code = kwargs.get('lot_code')
    db_name = kwargs.get('db_name')
    lo_id = kwargs.get('id')
    time_stamp = int(time.time()*1000)
    key = 'lotCode={}&lotGroupCode={}&timestamp={}&token=noget&key=cC0mEYrCmWTNdr1BW1plT6GZoWdls9b&'.format(lot_code, 0,
                                                                                                            time_stamp)
    sign = get_sign(key)
    post_data = {
        'token': 'noget',
        'timestamp': time_stamp,
        'lotGroupCode': 0,
        'lotCode': lot_code,
        'sign': sign.upper()
    }
    data = get_open_data(url, post_data)
    if data:
        try:
            issue = data['data']['preDrawIssue']
            open_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['data']['preDrawTime'] / 1000))
            open_code = data['data']['preDrawCode']
            cp_id = open_code.replace(',', '')
            open_url = 'https://www.cpyzj.com/open-awards-detail.html?lotCode={}&lotGroupCode=1'.format(lot_code)
            item = {
                'cp_id': cp_id,
                'cp_sn': '18' + issue,
                'expect': issue,
                'open_time': open_time,
                'open_code': open_code,
                'open_url': open_url,
                'create_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            save_data(url, db_name, item)
        except Exception as e:
            _logger.error('parse error: %s' % Util.traceback_info(e))


def main():
    lo_dict = {
        'gd11x5': 10006,
        'jsk3': 10007,
        'bjkl8': 10014,
        'jx11x5': 10015,
        'js11x5': 10016,
        'ah11x5': 10017,
        'sh11x5': 10018,
        'ln11x5': 10019,
        'hb11x5': 10020,
        'gx11x5': 10022,
        'jl11x5': 10023,
        'nmg11x5': 10024,
        'zj11x5': 10025,
        'gxk3': 10026,
        'jlk3': 10027,
        'hebk3': 10028,
        'nmgk3': 10029,
        'ahk3': 10030,
        'fjk3': 10031,
        'hbk3': 10032,
        # 'bjk3': 10033,
        'tjklsf': 10034,
        # 'bjpks': 10001,
        # 'cqssc': 10002,
        # 'tjssc': 10003,
        # 'xjssc': 10004,
        'gdklsf': 10005,
        # 'sd11x5': 10008,
        'cqklsf': 10009,
        'gxklsf': 10038
    }
    id_dict = {
        'gd11x5': 7,
        'jsk3': 79,
        'bjkl8': 100,
        'jx11x5': 46,
        'js11x5': 87,
        'ah11x5': 89,
        'sh11x5': 86,
        'ln11x5': 53,
        'hb11x5': 42,
        'gx11x5': 112,
        'jl11x5': 54,
        'nmg11x5': 52,
        'zj11x5': 88,
        'gxk3': 73,
        'jlk3': 81,
        'hebk3': 83,
        'nmgk3': 82,
        'ahk3': 78,
        'fjk3': 77,
        'hbk3': 74,
        'bjk3': 84,
        'tjklsf': 65,
        'bjpks': 3,
        'cqssc': 68,
        'tjssc': 69,
        'xjssc': 66,
        'gdklsf': 35,
        # 'sd11x5': 10008,
        'cqklsf': 62,
        'gxklsf': 36
    }
    for key, value in lo_dict.items():
        info = mysql.select('t_lottery', condition=[('id', id_dict[key])], fields=['lottery_result'], limit=1)
        db_name = info.get('lottery_result')
        if db_name:
            kwargs = {
                'lot_code': value,
                'db_name': db_name,
                'id': id_dict[key]
            }
            url = 'https://www.cpyzj.com/req/cpyzj/lotHistory/queryNewestLotByCode'
            get_newest_data(url, **kwargs)


if __name__ == '__main__':
    while 1:
        main()
        time.sleep(120)
