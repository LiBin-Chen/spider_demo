#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

# if __name__ == '__main__':
#     print 'Access Denied.'
#     sys.exit()

import os, datetime, logging
from logging.handlers import RotatingFileHandler

DEBUG = True
APP_ROOT = getattr(sys, '__APP_ROOT__', os.path.split(os.path.realpath(__file__))[0])

APP_PATH = getattr(sys, '__APP_PATH__', os.path.join(APP_ROOT, 'packages'))

APP_PATH and sys.path.insert(0, APP_PATH)
'''
消息队列相关
'''
# 队列主机地址
# QUEUE_HOST =

# 队列主机
AMQP_URL = 'amqp://guest:guest@127.0.0.1:5672/'   #本地测试
# 更新xunsearch
PUT_XS_HQCHIP = 'put_xunsearch'
# 更新或建立迅搜索引
PUT_XS_QUEUE = 'update_xunsearch'
# 抓取代理待处理队列
PROXY_QUEUE = 'search_proxy'
# 待抓取热门数据
HOT_QUEUE = 'hot_goods'
# 待更新
UPDATE_QUEUE = 'default_goods'
# 已更新待同步
WAIT_UPDATE_QUEUE = 'wait_post_goods'
# 等待在各个网站搜索的关键词队列
SEARCH_QUEUE = 'search_queue'
# 搜索需要更新的数据队列
SEARCH_UPDATE_QUEUE = 'search_update_queue'
# 搜索后不是列表而是分类的地址，放入队列重新在抓取
SEARCH_LIST_QUEUE = 'search_list'
# 在各个网站搜索的彩种开奖地址,抓取后放到postNewQueue队列中提交到网站
SEARCH_GOODS_QUEUE = 'search_goods'
# 等待向线上提交的新增的数据
WAIT_ADD_QUEUE = 'wait_post_new_goods'
# 错误数据
DELETE_QUEUE = 'delete_goods'
# 等待发送的email
SEND_EMAIL = 'send_email'
# 队列每次推送数量
QUEUE_LIMIT = 100

get_sports_info = lambda id: DB_KEY[int(str(id)[0:2])] if int(str(id)[0:2]) in DB_KEY else None
get_web_url = lambda id: URL_KEY[int(str(id)[0:2])] if int(str(id)[0:2]) in URL_KEY else None


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
        {  # 本地测试数据库
            'user': 'root',
            'passwd': 'root',
            'host': '127.0.0.1',
            'port': 3306,
            'charset': 'utf8',
            'db': 'lottery_info_spider',
            'tablepre': '',
            'db_fields_cache': False,
        },
        {  # 开发数据库
            'host': '192.168.2.22',
            'user': 'root',
            'passwd': 'root',
            'port': 3306,
            'charset': 'utf8',
            'db': 'lottery_info',
            'tablepre': '',
            'db_fields_cache': False,
        },
    ),
    'localhost': {
        # ------------- localhost 本地跑数据使用
        'host': 'localhost',
        'user': 'root',
        'passwd': 'root',
        'port': 3306,
        'charset': 'utf8',
        'db': 'test',
        'tablepre': '',
        'db_fields_cache': False,
        'data_type': 'dict',
    },
    'sqlite': 'database.db',
    # mongodb://[username:password@]host1[:port1][,host2[:port2],…[,hostN[:portN]]][/[database][?options]]
    # 本地测试数据库
    'mongo': (
        'mongodb://localhost:27017/spider_',
    ),
}

DB_KEY = {
    # 10: 'cpyzwl',
    11: 'cpsll',  # https://cp.360.cn/
    12: 'cpaicai',  # http://www.aicai.com/
    13: 'cp5ll',  # http://datachart.500.com/
    14: 'cpcwl',  # http://www.cwl.gov.cn/
    15: 'cpjsh',  # https://www.jsh365.com/
    16: 'pks',  # https://www.jsh365.com/
    # 16: '',
    # 17: '',
    # 18: '',
    # 19: '',
}
URL_KEY = {
    # 10: 'cpyzwl',
    11: 'jsh',
    12: 'sll',
    13: 'aicai',
    14: 'cwl',
    15: 'five',
    16: 'pks',
    17: 'gov',  # 体彩
    18: 'cpyzj',  # 彩票易中奖
    19: 'xjfc',  # 新疆福彩
    20: 'gxfc',  # 广西福彩
    21: 'zjfc',  # 浙江福彩
    22: 'gdfc',  # 广东福彩
    23: 'bjfc',  # 北京福彩
    24: 'tjfc',  # 天津福彩
}

SPORTS_SITE = {
    10: '',
    11: '',
    12: '',
    13: '',
    14: '',
    15: '',
    16: '',
    17: '',
    18: '',
    19: '',
    20: '',
    21: '',
    22: '',
    23: '',
    24: '',
    26: '',
    27: '',
    28: '',
    29: '',
    30: '',
    31: '',
    32: '',
    33: '',
    34: '',
    35: '',
    36: '',
    37: '',
    38: '',
    39: '',
    40: '',
    41: '',
    42: '',
    43: '',

}

# 数据更新时间间隔
DTI = {
    10: '',
    11: '',
    12: '',
    13: '',
    14: '',
    15: '',
    16: '',
    17: '',
    18: '',
    19: '',
    20: '',
    21: '',
    22: '',
    23: '',
    24: '',
    27: '',
    29: '',
    30: '',
    32: '',
    33: '',
    34: '',
    35: '',
    36: '',
    37: '',
    38: '',
    39: '',
    40: '',
    41: '',
    42: '',
    43: '',
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
        filename=os.path.join(LOGDIR, 'spider_' + datetime.datetime.now().strftime("%Y-%m-%d_%H") + ".log"), mode='a+', maxBytes=1024*1024*5, backupCount=20)
    _handler.setFormatter(
        logging.Formatter(fmt='>>> %(asctime)-10s %(name)-12s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
    LOG = logging.getLogger('yzwl_spider')
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
    'SMTP_USER': '18878554519@163.com',
    'SMTP_PASSWORD': '',
    'SMTP_DEBUG': True,
    'SMTP_FROM': '18878554519@163.com',
}

EMAIL_NOTICE = {
    # 接收人员邮箱地址列表
    'accept_list': (
        # 'qaulau@qq.com',
        # 'qaulau@139.com',
        # '373799302@qq.com',
        '306333914@qq.com',
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
