# -*- coding: utf-8 -*-
# @Time    : 2019/3/28 17:04
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : yzfc.py
# @Software: PyCharm
# @Remarks : 燕赵福彩网

from lxml import etree
from packages import Util


session = Util.get_session()


def _parse_detail_data(url, num_data, prize_data, **kwargs):
    lo_type = kwargs.get('lo_type')
    open_details_url = url
    if lo_type == "ssq":
        open_code = ','.join(v['value'] for v in num_data[:6]) + '+' + num_data[7]['value']
        open_time = num_data[7]['value'] + ' 21:15:00'
        cp_sn = '19' + kwargs['expect']
        cp_id = ''.join(v['value'] for v in num_data[:7])
        open_result = {
            'rolling': num_data[9]['value'],
            'xj_sale': num_data[8]['value'],
            'total_sale': num_data[10]['value'],
            'prizes': prize_data
        }
    elif lo_type == 'fc3d':
        open_code = ','.join(v['value'] for v in num_data[:3])
        open_time = num_data[6]['value'] + ' 21:15:00'
        cp_sn = '19' + kwargs['expect']
        cp_id = ''.join(v['value'] for v in num_data[:3])
        open_result = {
            'xj_sale': num_data[7]['value'],
            'currentAward': num_data[8]['value'],
            'prizes': [prize.pop('allNumber') for prize in prize_data]
        }
    elif lo_type == 'threeX7':
        open_code = ','.join(v['value'] for v in num_data[:7]) + '+' + num_data[7]['value']
        open_time = num_data[8]['value'] + ' 00:00:00'
        cp_sn = '19' + kwargs['expect']
        cp_id = ''.join(v['value'] for v in num_data[:8])
        open_result = {
            'rolling': num_data[10]['value'],
            'xj_sale': num_data[9]['value'],
            'prizes': [prize.pop('allNumber') for prize in prize_data]
        }
    elif lo_type == 'qlc':
        open_code = ','.join(v['value'] for v in num_data[:7]) + '+' + num_data[7]['value']
        open_time = num_data[8]['value'] + ' 21:15:00'
        cp_sn = '19' + kwargs['expect']
        cp_id = ''.join(v['value'] for v in num_data[:8])
        open_result = {
            'rolling': num_data[10]['value'],
            'total_sale': num_data[11]['value'],
            'prizes': [prize.pop('allNumber') for prize in prize_data]
        }
    elif lo_type == 'twoX7':
        open_code = ','.join(v['value'] for v in num_data[:7])
        open_time = num_data[7]['value'] + ' 00:00:00'
        cp_sn = '19' + kwargs['expect']
        cp_id = ''.join(v['value'] for v in num_data[:6])
        open_result = {
            'rolling': num_data[11]['value'] + num_data[10]['value'],
            'total_sale': num_data[9]['value'],
            'prizes': [prize.pop('allNumber') for prize in prize_data]
        }


def api_fetch_data(url, proxy=None, **kwargs):
    number_api_url = 'http://www.yzfcw.com/getLotteryNumber'
    detail_api_url = 'http://www.yzfcw.com/getLotteryDetailInfo'
    game_id = {
        'ssq': 1,
        'fc3d': 2,
        'qlc': 3,
        '20x5': 4,
        'hyc': 5,
        'pl5': 7,
        'pl7': 8
    }
    lo_type = kwargs.get('lo_type')
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        lottery_id = selector.xpath('//*[@id="{}Select"]/option[1]/@value'.format(lo_type))[0]
        expect = selector.xpath('//*[@id="{}Select"]/option[1]/text()'.format(lo_type))[0]
        number_post_data = {'lotteryId': lottery_id}
        detail_post_data = {'lotteryId': lottery_id, 'gameId': game_id[lo_type]}
        kwargs['expect'] = expect
        num_r = session.post(number_api_url, number_post_data)
        num_data = num_r.json()
        detail_r = session.post(detail_api_url, detail_post_data)
        detail_data = detail_r.json()
        _parse_detail_data(url, num_data, detail_data)


def main():
    lottery_list = ['ssq', 'fc3d', 'hyc', 'qlc', 'pl5', 'pl7']
    for lottery in lottery_list:
        index_url = 'http://www.yzfcw.com/game/{}Index'.format(lottery)
        api_fetch_data(index_url)
