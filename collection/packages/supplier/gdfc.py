# -*- coding: utf-8 -*-
# @Time    : 2019/4/8 14:17
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : gdfc.py
# @Software: PyCharm
# @Remarks : 广东福彩
from lxml import etree
from packages import Util

session = Util.get_session()


def main():
    url = 'http://www.gdfc.org.cn/'
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        ssq_url = selector.xpath('//*[@id="drawName-ssq"]/a/@href')



if __name__ == '__main__':
    pass