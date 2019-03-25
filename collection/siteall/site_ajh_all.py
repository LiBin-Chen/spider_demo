# -*- coding: utf-8 -*-
# @Time    : 2019/3/22 18:11
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_ajh_all.py
# @Software: PyCharm
# @Remarks : A计划网站数据爬虫
import os
import sys


try:
    from packages import yzwl, Util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    from packages import yzwl, Util

session = Util.get_session('http://www.556955.com/')


def get_result(data):
    plan = data['data']['plan']
    for p in plan:
        win = p.get('win', 0)
        if win == 0:
            status = '等开'
        else:
            status = '中' if win else '错'
        result = {
            'status': status,

        }

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
            get_result(data)


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
