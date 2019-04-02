# -*- coding: utf-8 -*-
# @Time    : 2019/3/22 18:11
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_ajh_all.py
# @Software: PyCharm
# @Remarks : A计划网站数据爬虫
import logging
import os
import sys
import time

try:
    from packages import yzwl, Util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    from packages import yzwl, Util

session = Util.get_session('http://www.556955.com/')
db = yzwl.DbClass()
mysql = db.local_yzwl
_logger = logging.getLogger('yzwl_spider')


def save_to_db(item, db_name):
    mysql.insert(db_name, data=item)
    _logger.info('INFO:数据保存成功, 结果:%s' % item['desc'])


def get_result(data, lo_type, **kwargs):
    try:
        lottery_dict = {
            'jsk3': '江苏快3',
            'ahk3': '安徽快3',
            'gxk3': '广西快3',
            'hbk3': '湖北快3',
            'bjk3': '北京快3',
            'hebk3': '河北快3',
            'gsk3': '甘肃快3',
            'shk3': '上海快3',
            'gzk3': '贵州快3',
            'jlk3': '吉林快3',
            'cqssc': '重庆时时彩',
            'tjssc': '天津时时彩',
            'xjssc': '新疆时时彩',
            'pk10': '北京pk10',
            'xyft': '幸运飞艇',
            'gd11x5': '广东11选5',
            'sd11x5': '山东11选5',
            'sh11x5': '上海11选5',
            'jx11x5': '江西11选5',
        }
        plan = data['data']['plan']
        for p in plan:
            win = p.get('win', 0)
            if win == 0:
                status = '等开'
            else:
                status = '中' if win else '错'
            plans = ' '.join(map(str, p['plans']))
            start_issue = p['beginIssue']
            end_issue = p['endIssue']
            win_issue = p['winIssue']
            plan_name = data['data']['planName']
            result = '{}-{}期 {} 【{}】 {}'.format(start_issue[-3:], end_issue[-3:],
                                                plan_name, plans, status)
            item = {
                'lottery_type': lottery_dict.get(kwargs['code']),
                'plan_name': plan_name,
                'start_expect': start_issue,
                'end_expect': end_issue,
                'win_expect': win_issue,
                'result': plans,
                'desc': result
            }
            # print(result)
            save_to_db(item, 't_lottery_ajh')
    except Exception as e:
        print(e)


def api_fetch_data(**kwargs):
    t = kwargs.get('type')
    code = kwargs.get('code')
    plan_dict = {
        'k3': [x for x in range(3)],
        'ssc': [x for x in range(10)],
        'pk10': [x for x in range(12)],
        '11x5': [x for x in range(3)]
    }
    for i in plan_dict[t]:
        url = 'http://www.556955.com/plan/api.do?code={}&plan={}&size=50&planSize=50'.format(code, i)
        r = session.get(url)
        if r.status_code == 200:
            data = r.json()
            get_result(data, t, **kwargs)
            time.sleep(1)


def main(**kwargs):
    type_dict = {
        'k3': ['jsk3', 'ahk3', 'gxk3', 'hbk3', 'bjk3', 'hebk3', 'gsk3', 'shk3', 'gzk3', 'jlk3'],
        'ssc': ['cqssc', 'tjssc', 'xjssc'],
        'pk10': ['pk10', 'xyft'],
        '11x5': ['gd11x5', 'sd11x5', 'sh11x5', 'jx11x5']
    }
    for key, value in type_dict.items():
        kwargs['type'] = key
        for v in value:
            kwargs['code'] = v
            api_fetch_data(**kwargs)
    pass


if __name__ == '__main__':
    main()
