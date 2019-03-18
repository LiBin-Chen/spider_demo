# -*- coding: utf-8 -*-

import json
import logging
import random
import time

import requests

from packages import DbSession, yzwl

db = DbSession()
# pro_collection=db.mongo['proxies']
collection = db.mongo['pay_proxies']
collection.ensure_index('ip')

_header = {
    'Host': 'proxy.elecfans.net',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
}

collection = db.mongo['pay_proxies']
# collection = db.mongo['proxies']
db = yzwl.DbClass()
mysql = db.yzwl

db_name = 'proxies'
_logger = logging.getLogger('yzwl_spider')
def get_prolist(limit):
    """获取代理列表"""
    prodict = {}
    url = 'http://proxy.elecfans.net/proxys.php?key=nTAZhs5QxjCNwiZ6&num=10&type=pay'
    proxies={'https': 'https://121.206.7.28:41590'}
    # proxies = None
    try:
        resp = requests.get(url, headers=_header, proxies=proxies)
        print(resp)
        data = json.loads(resp.content)

        for vo in data['data']:
            ip = vo['ip']
            # print('ip', ip)
            prodict = {
                'ip': ip
            }
            item = {
                'ip': vo['ip'],
                'is_pay': 1,
                'is_use': 1,
                'create_time': int(time.time()),
            }
            info = collection.find_one({'ip': ip})
            if info:
                _logger.info('INFO:数据已存在不做重复存入')
                continue
            collection.save(prodict)
            mysql.insert(db_name, data=item)
            _logger.info('INFO:数据保存成功')
    except:
        print('获取错误')


while 1:
    # limit = random.randint(100, 250)
    limit = 10
    get_prolist(limit)
    # sleep_time = random.randint(10, 40)
    time.sleep(5)
