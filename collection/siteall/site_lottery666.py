# -*- coding: utf-8 -*-
# @Time    : 2019/3/26 9:53
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_lottery666.py
# @Software: PyCharm
# @Remarks : 彩票资讯
from lxml import etree

from packages import Util

session = Util.get_session()


def get_article(art_id):
    url = 'https://m.lottery666.com/toutiao/{}.html'.format(art_id)
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        title = selector.xpath("//div[@class='title']/text()")
        date = selector.xpath("//div[@class='date']/span[2]/text()")
        article = selector.xpath("//div[@class='content']")
        article_str = etree.tostring(article[0], encoding='utf8')
        pass


def get_article_url(pages):
    id_list = []
    for page in range(1, pages+1):
        url = 'https://api.lottery666.com/iation/haocai/load?page={}&identity=com.houcai.letoula&platform=3'.format(page)
        r = session.get(url)
        if r.status_code == 200:
            data = r.json()
            for d in data['data']['loading']:
                id_list.append(d['articleId'])
    for art_id in id_list:
        get_article(art_id)


if __name__ == '__main__':
    get_article_url(2)
