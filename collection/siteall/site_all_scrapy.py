# -*- coding: utf-8 -*-

"""

www.test.com整站数据爬虫
本代码仅作参考
requirements:
    scrapy>=1.2.0
    lxml
"""

import os
import re
import sys
import copy
import json
import base64
import scrapy
import random
import logging
import hashlib
import requests
import argparse
from scrapy.http import Request
from requests.utils import proxy_bypass
from scrapy.utils.python import to_bytes
from six.moves.urllib.parse import unquote
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.httpobj import urlparse_cached
from scrapy.exceptions import DropItem, IgnoreRequest, NotConfigured

try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy

try:
    import config
    from queue import Queue
    from packages import yzwl
    from packages import rabbitmq
    from packages import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import config
    from queue import Queue
    from packages import rabbitmq
    from packages import Util as util
    from packages import yzwl



sys.__APP_LOG__ = False

_logger = logging.getLogger('demo_spider')
mq = rabbitmq.RabbitMQ()
db = yzwl.DbClass()

settings = {
    'BOT_NAME': 'demospider',
    'ROBOTSTXT_OBEY': False,
    'COOKIES_ENABLED': True,
    'CONCURRENT_ITEMS': 100,
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_TIMEOUT': 30,
    'DOWNLOAD_DELAY': 1,

    'DEFAULT_REQUEST_HEADERS': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
    },
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',

    'DOWNLOADER_MIDDLEWARES': {
        __name__ + '.IgnoreRquestMiddleware': 1,
        __name__ + '.UniqueRequestMiddleware': 3,
        __name__ + '.RandomUserAgentMiddleware': 5,
        # __name__ + '.ProxyRequestMiddleware': 8,
    },
    'ITEM_PIPELINES': {
        __name__ + '.MetaItemPipeline': 500,
    },
    'EXTENSIONS': {
        'scrapy.extensions.closespider.CloseSpider': 500,
    },
    'TELNETCONSOLE_ENABLED': False,
    'LOG_LEVEL': logging.DEBUG,

    # 'SCHEDULER': "scrapy_rabbitmq.scheduler.Scheduler",
    # 'SCHEDULER_PERSIST': True,
    # 'SCHEDULER_QUEUE_CLASS': 'scrapy_rabbitmq.queue.SpiderQueue',

}
# 过滤规则
filter_rules = (
    'https://www.test.me/',
    '/',

)
proxy_rules = (
    '/',
)


class RandomUserAgentMiddleware(object):
    """随机UserAgent中间件"""

    def __init__(self, agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        if 'USER_AGENT_LIST' in crawler.settings:
            agents = crawler.settings.getlist('USER_AGENT_LIST')
        else:
            agents = config.USER_AGENT_LIST
        return cls(agents)

    def process_request(self, request, spider):
        if self.agents:
            request.headers.setdefault('User-Agent', random.choice(self.agents))


class IgnoreRquestMiddleware(object):
    """忽略请求url"""

    def __init__(self, crawler):
        global filter_rules
        self.filters = []
        for rule in filter_rules:
            self.filters.append(re.compile(rule))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        _ignore = True
        for vo in self.filters:
            if vo.search(request.url) or request.url in spider.start_urls:
                _ignore = False
                break
        if _ignore:
            raise IgnoreRequest("ingore repeat url: %s" % request.url)


class UniqueRequestMiddleware(object):
    """去重请求中间件"""

    def __init__(self, crawler):
        name = 'spider_' + crawler.spider.name + '_item'
        self.mongo = yzwl.db.mongo[name]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def close_spider(self, spider):
        del self.mongo

    def process_request(self, request, spider):
        url = to_bytes(request.url.split('#')[0])
        key = hashlib.md5(url).hexdigest()
        info = self.mongo.find_one({'key': key})
        if info:
            _logger.warn("ingore repeat url: %s" % request.url)
            raise IgnoreRequest("ingore repeat url: %s" % request.url)


class ProxyRequestMiddleware(object):
    """代理请求中间件"""

    def __init__(self, crawler):
        if not settings.getbool('USE_PROXY'):
            raise NotConfigured
        self.queue = Queue()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        proxies = {}
        try:
            data = self.queue.get(block=False)
            proxy = self._get_proxy(data['ip'], 'http')
            proxies['http'] = proxy
            proxies['https'] = proxy
        except:
            self._fill_queue(60)
        self._set_proxy(request, proxies)

    def _fill_queue(self, limit_num=30):
        """填充队列"""
        resp = requests.get('http://test.com?key=&num={0}'.format(limit_num))
        dlist = json.loads(resp.text)['data']
        for vo in dlist:
            self.queue.put({'ip': vo['ip']})

    def _get_proxy(self, url, orig_type):
        proxy_type, user, password, hostport = _parse_proxy(url)
        # proxy_url = urlparse.urlunparse((proxy_type or orig_type, hostport, '', '', '', ''))
        if user:
            user_pass = to_bytes(
                '%s:%s' % (unquote(user), unquote(password)),
                encoding=self.auth_encoding)
            creds = base64.b64encode(user_pass).strip()
        else:
            creds = None
        # return creds, proxy_url

    def _set_proxy(self, request, proxies):
        if not proxies:
            return
        parsed = urlparse_cached(request)
        scheme = parsed.scheme
        if scheme in ('http', 'https') and proxy_bypass(parsed.hostname):
            return
        if scheme not in proxies:
            return
        creds, proxy = proxies[scheme]
        request.meta['proxy'] = proxy
        if creds:
            request.headers['Proxy-Authorization'] = b'Basic ' + creds


class GoodsItem(scrapy.Item):
    demo = scrapy.Field()  # 定义存储数据字段


class MetaItemPipeline(object):
    """数据集管道"""

    def __init__(self, crawler):
        name = 'spider_' + crawler.spider.name + '_item'
        # self.mongo = yzwl.db.mongo[collection_name]
        # self.mongo.ensure_index('demo', unique=True)  #通常使用非关系型数据库作为去重
        self.mysql = db.yzwl

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        """保存数据"""
        demo = item.get('demo')
        if not demo:
            raise DropItem("item data type error")
        # self.put_queue(item)
        data = copy.deepcopy(dict(item))
        if not data:
            raise DropItem("item data is empty")

        # info = self.mongo.find_one({'demo': data['demo']})
        demo_test = item.get('demo_test', '')
        if not demo_test:
            raise DropItem("demo_test is empty")
            # return
        condition = {'demo': demo}
        try:
            info = self.mysql.select(demo_test, condition=condition, limit=1)
            if not info:
                # self.mongo.insert(data)
                item['create_time'] = util.date()
                item['update_time'] = util.date()
                self.mysql.insert(demo_test, data=item)
                # _logger.info('success insert mysql : %s' % data['demo'])
            else:
                item['create_time'] = info['create_time']
                item['update_time'] = util.date()
                # self.mongo.update({'_id': info['_id']}, {"$set": data})
                self.mysql.update(demo_test, condition=condition, data=item)
                # _logger.info('success update mysql : %s' % data['demo'])
        except Exception as e:
            _logger.info('error op mysql : {0}  : e {1}'.format(data['demo'], e))
        raise DropItem('success process')

    # def put_queue(self, queue_list):
    #     '''提交到队列'''
    #     qname = 'wait_post_goods'
    #     try:
    #         mq.put(qname, queue_list)
    #         print('提交队列{0}成功'.format(qname))
    #     except:
    #         print('提交队列{0}失败'.format(qname))

    def close_spider(self, spider):
        # del self.mongo
        del self.mysql
        pass


class DemoSpider(CrawlSpider):
    name = 'demo'
    allowed_domains = ['www.test.me', 'https://www.test.me/']
    # 类别页面
    start_urls = ['https://www.test.me/']

    def __init__(self, name=None, **kwargs):
        self.mysql = db.local_yzwl
        self.head_url = 'https://www.test.me'
        self._init_args(**kwargs)
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }
        super(DemoSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        self.abbreviation = kwargs.get('ABBREVIATION', '')
        self.start_date = kwargs.get('START_DATE', '')
        self.end_date = kwargs.get('END_DATE', '')
        self.end_date = self.end_date if self.end_date else util.date()

        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback='parse_resp', follow=True),
        )

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, headers=self.headers, callback=self.parse_resp)

    def parse_resp(self, resp):
        '''
        第一层处理,类别获取后进行下一层抓取
        :param resp: 
        :return: 
        '''
        item = GoodsItem()
        category = []
        date_list = util.specified_date(self.start_date, end_date=self.end_date)
        for category_url in category:
            if self.abbreviation and self.abbreviation not in category_url:
                # 非指定的数据不进行抓取(指定彩种的情况下使用该选项)
                continue

            '''
            抓取规则
            '''
            today_url = ''
            # 获取保存的数据库
            result_key = category_url.split('-')[1]
            demo_test = config.PKS_KEY_DICT.get(result_key, '')

            for history_date in date_list:
                date_time = ''.join(history_date.split('-'))
                url = today_url.replace('today', date_time)
                yield scrapy.Request(url=url, headers=self.headers, callback=self.parse_product,
                                     meta={'item': item})

    def code_util(self, open_code_list):
        '''开奖号码处理'''
        open_code = '1,2,3'
        return open_code

    def parse_product(self, resp):
        '''
        第二层的数据获取/如需继续获取下一层数据请调用 parse_detail 进行解析
        :param resp: 
        :return: 
        '''
        item = resp.meta.get('item')

        item = {
            'demo': ''
        }

        yield item

    def parse_detail(self, resp):
        '''
        详情页解析  暂无20190428
        :param resp:
        :return:
        '''
        item = resp.meta.get('item')
        if item is None:
            item = GoodsItem()
        if not resp.status == 200:
            return

    @property
    def closed(self):
        """蜘蛛关闭清理操作"""

        def wrap(reason):
            # del self.queue
            del self.mysql
            pass

        return wrap


def main():
    global settings
    from scrapy import cmdline
    from scrapy.settings import Settings

    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)

    act_group = parser.add_argument_group(title='操作选项组')
    act_group.add_argument('-r', '--run', dest='cmd', help='运行爬虫获取数据',
                           action='store_const', const='runspider')
    act_group.add_argument('-s', '--shell', dest='cmd', help='控制台调试',
                           action='store_const', const='shell')
    act_group.add_argument('-v', '--view', dest='cmd', help='使用浏览器打开蜘蛛获取的URL页面',
                           action='store_const', const='view')

    run_group = parser.add_argument_group(title='运行操作组')
    run_group.add_argument('-n', '--limit-num', dest='limit', default=0,
                           help='限制总请求次数，默认为0不限制', type=int)
    run_group.add_argument('-m', '--max-request-num', dest='max', default=30,
                           help='同时最大请求数，默认为30，0则不限制', type=int)
    run_group.add_argument("-a", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                           help="设置爬虫参数（可以重复）")
    run_group.add_argument("-o", "--output", metavar="FILE",
                           help="输出 items 结果集 值FILE (使用 -o 将定向至 stdout)")
    run_group.add_argument("-t", "--output-format", metavar="FORMAT",
                           help="基于 -o 选项，使用指定格式输出 items")
    run_group.add_argument('-d', '--dist', help='分布式运行，用于其他进程提交数据',
                           action='store_true', default=False)
    run_group.add_argument('-p', '--proxy', help='使用代理进行请求', action='store_true', default=False)

    opt_group = parser.add_argument_group(title='可选项操作组')
    opt_group.add_argument('-S', '--start-date', default='04/25/2019', help='设置起始分类索引值，默认04/24/2019', )
    opt_group.add_argument('-E', '--end-date', default=None, help='设置截止日期索引值，默认截止目前', )
    opt_group.add_argument('-A', '--abbreviation', default=None, help='指定产品,产品 keyword', )

    gen_group = parser.add_argument_group(title='通用选择项')
    gen_group.add_argument('-u', '--url', help='设置URL，运行操作设置该项则为起始爬取URL，\
                                                                    调试操作设置则为调试URL，查看操作则为打开查看URL')

    args = parser.parse_args()
    if args.help:
        parser.print_help()
    elif args.cmd:
        settings = Settings(settings)
        if args.cmd == 'runspider':
            argv = [sys.argv[0], args.cmd, sys.argv[0]]
            for vo in run_group._group_actions:
                opt = vo.option_strings[0]
                val = args.__dict__.get(vo.dest)
                if val == vo.default:
                    continue
                if isinstance(val, (list, tuple)):
                    val = ' '.join(val)
                if vo.dest == 'limit':
                    settings['CLOSESPIDER_ITEMCOUNT'] = val
                    continue
                elif vo.dest == 'max':
                    settings['CONCURRENT_REQUESTS'] = val
                    continue
                elif vo.dest == 'dest':
                    settings['DESTRIBUT_RUN'] = val
                    continue
                elif vo.dest == 'proxy':
                    settings['USE_PROXY'] = val
                    continue
                argv.extend([opt, val])

            if args.url:
                argv.extend(['-a', 'START_URL=%s' % args.url])
            if args.start_date:
                argv.extend(['-a', 'START_DATE=%s' % args.start_date])
            if args.end_date:
                argv.extend(['-a', 'END_DATE=%s' % args.end_date])
            if args.abbreviation:
                argv.extend(['-a', 'ABBREVIATION=%s' % args.abbreviation])
        elif args.cmd == 'shell':
            argv = [sys.argv[0], args.cmd]
            if args.url:
                argv.append(args.url)
        elif args.cmd == 'view':
            if not args.url:
                print('please setting --url option')
                return None
            argv = [sys.argv[0], args.cmd, args.url, args.sd, args.ed]
        cmdline.execute(argv, settings)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
