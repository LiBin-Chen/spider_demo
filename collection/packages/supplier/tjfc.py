# -*- coding: utf-8 -*-
# @Time    : 2019/4/8 16:51
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : tjfc.py
# @Software: PyCharm
# @Remarks : 天津福彩

from lxml import etree
from packages import Util


session = Util.get_session()


def api_fetch_data(url, **kwargs):
    post_data = {
        'termCode': kwargs.get('expect'),
        'playId': kwargs.get('id')
    }
    r = session.post(url, post_data)
    if r.status_code == 200:
        data = r.json()
        pass


def main():
    url = 'http://www.tjflcpw.com/index.aspx'
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        ssq_expect = selector.xpath('//*[@id="form1"]/div[4]/div[3]/div[2]/div/div[1]/div[1]/span[2]/a/text()')[0]
        fc3d_expect = selector.xpath('//*[@id="form1"]/div[4]/div[3]/div[2]/div/div[2]/div[1]/span/a/text()')[0]
        qlc_expect = selector.xpath('//*[@id="form1"]/div[4]/div[3]/div[2]/div/div[3]/div[1]/span[2]/a/text()')[0]
        lo_dict = {
            1: ssq_expect.replace('\r', '').replace('\n', '').replace(' ', '').replace('第', '').replace('期', ''),
            2: fc3d_expect.replace('\r', '').replace('\n', '').replace(' ', '').replace('第', '').replace('期', ''),
            3: qlc_expect.replace('\r', '').replace('\n', '').replace(' ', '').replace('第', '').replace('期', '')
        }
        for key, value in lo_dict.items():
            api_fetch_data('http://www.tjflcpw.com/Handlers/PlayInfoHandler.ashx', **{'expect': value, 'id': key})


if __name__ == '__main__':
    main()
