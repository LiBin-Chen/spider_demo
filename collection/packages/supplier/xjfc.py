# -*- coding: utf-8 -*-
# @Time    : 2019/3/28 15:13
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : xjfc.py
# @Software: PyCharm
# @Remarks : 新疆福彩网

from lxml import etree
from packages import Util


session = Util.get_session()


def api_fetch_data(url, proxy=None, **kwargs):
    number_api_url = 'http://www.xjflcp.com/getLotteryNumber'
    detail_api_url = 'http://www.xjflcp.com/getLotteryDetailInfo'
    lo_type = kwargs.get('lo_type')
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        lottery_id = selector.xpath('//*[@id="{}Select"]/option[1]/@value'.format(lo_type))[0]

def main():
    lottery_list = ['ssq', 'fc3d', 'threeX7', 'qlc', 'twoX7', 'ex7']
    for lottery in lottery_list:
        index_url = 'http://www.xjflcp.com/game/{}Index'.format(lottery)
        api_fetch_data(index_url)
