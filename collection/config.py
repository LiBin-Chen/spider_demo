#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

if __name__ == '__main__':
    print('Access Denied.')
    sys.exit()

import os, datetime, logging
from logging.handlers import RotatingFileHandler

DEBUG = True
APP_ROOT = getattr(sys, '__APP_ROOT__', os.path.split(os.path.realpath(__file__))[0])

APP_PATH = getattr(sys, '__APP_PATH__', os.path.join(APP_ROOT, 'packages'))

APP_PATH and sys.path.insert(0, APP_PATH)
'''
消息队列相关
'''

# 队列主机
AMQP_URL = 'amqp://guest:guest@127.0.0.1:5672'  # 本地

# 抓取代理待处理队列
PROXY_QUEUE = 'search_proxy'
# 默认队列
UPDATE_QUEUE = 'default_goods'
# 已更新待同步
WAIT_UPDATE_QUEUE = 'wait_post_goods'
# 等待在各个网站搜索的关键词队列
WAIT_ADD_QUEUE = 'wait_post_new_goods'
# 错误数据
DELETE_QUEUE = 'delete_goods'
# 等待发送的email
SEND_EMAIL = 'send_email'
# 队列每次推送数量
QUEUE_LIMIT = 50

'''
数据采集相关
'''
DATA_CACHE_TIME = 172800  # 抓取数据缓存时间,2天
USE_PROXY = True  # 是否使用代理

'''
数据库相关
'''
DATABASES = {
    'mysql': (
        {  # 开发数据库
            'host': '127.0.0.1',
            'user': 'root',
            'passwd': 'root',
            'port': 3306,
            'charset': 'utf8',
            'db': 'data_center',
            'tablepre': '',
            'db_fields_cache': False,
        },
        {  # 测试数据库
            'host': '127.0.0.1',
            'user': 'root',
            'passwd': 'root',
            'port': 3306,
            'charset': 'utf8',
            'db': 'data_center',
            'tablepre': '',
            'db_fields_cache': False,
        },
        {  # 本地数据库
            'user': 'root',
            'passwd': 'root',
            'host': '127.0.0.1',
            'port': 3306,
            'charset': 'utf8',
            'db': 'data_center',
            'tablepre': '',
            'db_fields_cache': False,
        },
    ),
    'sqlite': 'database.db',
    # 本地测试数据库
    'mongo': (
        'mongodb://localhost:27017/spider_',
    ),
}

DB_KEY = {
    10: 'DB10',  # db keyword
    11: 'DB11',
    12: 'DB12',
    13: 'DB13',
    14: 'DB14',
    15: 'DB15',
    16: 'DB16',

}
URL_KEY = {

    10: 'web10',  # web10 url
    11: 'web11',
    12: 'web12',
}

# 更新数据时使用
QNAME_KEY = {
    # 1: 'ALL',  # for all
    2: 'test_goods2',
    3: 'test_goods3',
    4: 'test_goods4',
    5: 'test_goods5',
    6: 'test_goods6',

}
# API数据缓存时间
DEAFULT_API_DATA_CHCHE_TIME = 1200 * 86400  # 默认值，下面没有配置的将使用这个值

API_DATA_CACHE_TIMES = {
    20: 365 * 5 * 86400,
    22: 5 * 86400,
}

'''
浏览器信息
'''
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/530.9 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/530.9',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/530.6 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/530.6',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/530.5',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/27.0.1453.93 Chrome/27.0.1453.93 Safari/537.36',
    # Ubuntu
    'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',  # IE10
    'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0))',  # IE9
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; InfoPath.2; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)',
    # IE8
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; InfoPath.2; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)',
    # IE7
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER',
    # 猎豹浏览器
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) '  # qq浏览器 ie 6
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) ',  # qq 浏览器 ie7
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15',  # firefox
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20130331 Firefox/21.0',  # firefox ubuntu
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0',  # firefox mac
    'Opera/9.80 (Windows NT 6.1; WOW64; U; en) Presto/2.10.229 Version/11.62',  # Opera windows
    # 'Googlebot/2.1 (+http://www.googlebot.com/bot.html)',# Google蜘蛛
    # 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)', #Bing蜘蛛
    # 'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)', #Yahoo蜘蛛
]

'''
日志配置
'''
APP_LOG = getattr(sys, '__APP_LOG__', True)
level = logging.DEBUG if DEBUG else logging.ERROR
LOGDIR = os.path.join(APP_ROOT, "logs")

# 仅应用日志
if APP_LOG:
    # 每小时一个日志
    _handler = RotatingFileHandler(
        filename=os.path.join(LOGDIR, 'spider_' + datetime.datetime.now().strftime("%Y-%m-%d_%H") + ".log"), mode='a+',
        maxBytes=1024 * 1024 * 5, backupCount=10)
    _handler.setFormatter(
        logging.Formatter(fmt='>>> %(asctime)-10s %(name)-12s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
    LOG = logging.getLogger('demo_spider')
    LOG.setLevel(level)
    LOG.addHandler(_handler)
    # 在控制台打印
    _console = logging.StreamHandler()
    LOG.addHandler(_console)

'''
邮件配置
'''
EMAIL = {
    'SMTP_HOST': 'smtp.163.com',
    'SMTP_PORT': 25,
    'SMTP_USER': 'test@163.com',
    'SMTP_PASSWORD': '',
    'SMTP_DEBUG': True,
    'SMTP_FROM': 'test@163.com',
}

EMAIL_NOTICE = {
    # 接收人员邮箱地址列表
    'accept_list': (
        'test@qq.com',
    )
}

'''
微信通知
'''
WEIXIN_NOTICE = {
    'accept_list': (
        '',
    ),
    'server': ''
}

SMT_DOMAIN = ''
SMT_API_KEY = ''
