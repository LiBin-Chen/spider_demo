# -*- coding: utf-8 -*-
# @Time    : 2019/4/3 15:33
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_cwl_news.py
# @Software: PyCharm
# @Remarks : 福彩网新闻爬虫
import re

from lxml import etree
from packages import Util

session = Util.get_session()


def get_news_list(page):
    url = 'http://www.cwl.gov.cn/xwzx/xwdt/index.shtml' if page == 1 else 'http://www.cwl.gov.cn/xwzx/xwdt/index_{}.shtml'.format(page)
    r = session.get(url)
    if r.status_code == 200:
        selector = etree.HTML(r.content.decode('utf8'))
        url_list = selector.xpath('//*[@id="content"]/div[1]/ul[1]/li/span[2]/a/@href')
        return url_list


def fetch_data(url, proxy=None, **kwargs):
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        title = selector.xpath('//*[@id="content"]/div[1]/h4/text()')[0]
        date_time = selector.xpath('//*[@id="content"]/div[1]/small[2]/text()')[0].replace('\xa0', '')
        article = selector.xpath('//*[@id="content"]/div[1]/div[2]')[0]
        etree.strip_attributes(article, 'style')
        result = etree.tostring(article, encoding='utf8').decode('utf8')
        result = re.findall(r'<p>.*</p>', result)[0]
        item = {
            'title': title,
            'datetime': date_time,
            'article': result,
            'source_url': url
        }


def main():
    pages = 1
    url_list = []
    for page in range(1, pages+1):
        url_list += get_news_list(page)
    for u in url_list:
        url = 'http://www.cwl.gov.cn' + u
        fetch_data(url)


if __name__ == '__main__':
    main()
