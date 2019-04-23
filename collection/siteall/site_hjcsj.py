# -*- coding: utf-8 -*-
# @Time    : 2019/4/22 10:17
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_hjcsj.py
# @Software: PyCharm
# @Remarks : 皇家彩世界 https://www.1395p.com/
import logging
import time

from lxml import etree
from packages import Util, yzwl

db = yzwl.DbClass()
# mysql = db.yzwl
local_mysql = db.local_yzwl
_logger = logging.getLogger('yzwl_spider')

session = Util.get_session()
session.headers.update({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Host': 'www.1395p.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
})
# session.proxies.update({
#     'http': 'http://127.0.0.1:1080',
#     'https': 'https://127.0.0.1:1080'
# })


def save_data(db_name, item):
    info = local_mysql.select(db_name, condition=[('expect', '=', item['expect'])], limit=1)
    if not info:
        local_mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号: %s ;' % (db_name, item['expect']))
    else:
        # mysql.update(db_name, condition=[('expect', '=', item['expect'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在, 期号: %s' % (db_name, item['expect']))


def fetch_data(url, **kwargs):
    db_name = kwargs.get('db_name')
    past = kwargs.get('past', 0)
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        data = selector.xpath('//*[@id="tbHistory"]/tbody/tr') if past else selector.xpath('//tr')
        for d in data:
            expect = d.xpath('./td[1]/i[1]/text()')[0]
            open_time = d.xpath('./td[1]/i[2]/text()')[0]
            numbers = d.xpath('./td[2]/div/span/text()')
            item = {
                'expect': expect.replace('-', ''),
                'open_time': Util.date(format='%Y-%m-%d') + ' ' + open_time + ':00',
                'open_code': ','.join(numbers),
                'open_url': url,
                'source_sn': 26,
                'create_time': Util.date(),
            }
            date_str, issue = expect.split('-')
            if int(issue) >= 72:
                item['open_time'] = Util.date(timestamp=time.mktime(time.strptime(date_str, '%Y%m%d'))+24*60*60, format='%Y-%m-%d') + ' ' + open_time + ':00'
            else:
                item['open_time'] = Util.date(timestamp=time.mktime(time.strptime(date_str, '%Y%m%d')), format='%Y-%m-%d') + ' ' + open_time + ':00'
            # 插入数据
            save_data(db_name, item)


def main(**kwargs):
    kwargs['past'] = 1
    past = kwargs.get('past', 0)
    kwargs['db_name'] = 'game_sdc_result'
    if past:
        # 获取历史数据
        sd = kwargs.get('sd', '7/17/2012')
        ed = kwargs.get('ed')
        date_list = Util.specified_date(sd, ed)
        for date in date_list:
            kwargs['date'] = date
            time_stamp = int(time.time() * 1000)
            url = 'https://www.1395p.com/sdc/kaijiang?date={}&_={}'.format(date, time_stamp)
            fetch_data(url, **kwargs)
            time.sleep(2)
    else:
        # 获取最新数据
        time_stamp = int(time.time()*1000)
        url = 'https://www.1395p.com/sdc/getnewestrecord?r={}'.format(time_stamp)
        fetch_data(url, **kwargs)


if __name__ == '__main__':
    main()
