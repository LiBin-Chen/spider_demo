# -*- coding: utf-8 -*-
# @Time    : 2019/3/26 9:53
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_lottery666.py
# @Software: PyCharm
# @Remarks : 彩票资讯 等待需求，未完成
import time

from lxml import etree

from packages import Util, yzwl

session = Util.get_session()

db = yzwl.DbClass()
# 本地库
mysql = db.local_yzwl


def save_data(item, db_name):
    info = mysql.select(db_name, condition=[('title', '=', item['title']), ('date', '=', item['date'])], limit=1)
    if not info:
        mysql.insert(db_name, data=item)
    else:
        print('数据已存在')


def get_article(art_id):
    url = 'https://m.lottery666.com/toutiao/{}.html'.format(art_id)
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        title = selector.xpath("//div[@class='title']/text()")[0]
        date = selector.xpath("//div[@class='date']/span[2]/text()")[0]
        articles = selector.xpath("//div[@class='content']/p")
        article_str = ''
        for article in articles[:-1]:
            article_str += etree.tostring(article, encoding='utf8').decode('utf8')
        item = {
            'title': title,
            'date': str(time.localtime().tm_year) + '-' + date,
            'content': article_str,
            'source_url': url
        }
        save_data(item, 't_lottery_news')


def get_article_url(pages):
    id_list = []
    for page in range(1, pages+1):
        url = 'https://api.lottery666.com/iation/haocai/load?page={}&' \
              'identity=com.houcai.letoula&platform=3'.format(page)
        r = session.get(url)
        if r.status_code == 200:
            data = r.json()
            for d in data['data']['loading']:
                id_list.append(d['articleId'])
    for art_id in id_list:
        get_article(art_id)


if __name__ == '__main__':
    get_article_url(2)
