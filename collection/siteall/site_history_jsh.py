# -*- coding: utf-8 -*-

"""
2019-04-25
www.jsh365.com整站数据爬虫

requirements:
    scrapy>=1.2.0
    lxml
"""

import os
import re
import sys
import argparse
import random
import logging
import hashlib
import copy
import threading

from requests.utils import proxy_bypass

try:
    from queue import Queue
    from packages import yzwl
    from packages import rabbitmq
    from packages import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    from queue import Queue
    from packages import rabbitmq
    from packages import Util as util
    from packages import yzwl

import json
import requests
import base64

try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import DropItem, IgnoreRequest, NotConfigured
from scrapy.http import Request
from scrapy.utils.python import to_bytes
# six
# from six.moves.urllib.request import getproxies, proxy_bypass
from six.moves.urllib.parse import unquote
from scrapy.utils.httpobj import urlparse_cached

sys.__APP_LOG__ = False
try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
    import config

_logger = logging.getLogger('yzwl_spider')
mq = rabbitmq.RabbitMQ()
db = yzwl.DbClass()

lock = threading.Lock()
settings = {
    'BOT_NAME': 'yzjshspider',
    'ROBOTSTXT_OBEY': False,
    'COOKIES_ENABLED': True,
    'CONCURRENT_ITEMS': 100,
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_TIMEOUT': 30,
    'DOWNLOAD_DELAY': 1,

    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'www.jsh365.com',
        'Upgrade-Insecure-Requests': '1',
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
    'https://www.jsh365.com',
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
        resp = requests.get('http://proxy.elecfans.net/proxys.php?key=nTAZhs5QxjCNwiZ6&num={0}'.format(limit_num))
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
    expect = scrapy.Field()  # 开奖期号
    open_time = scrapy.Field()  # 开奖时间
    open_code = scrapy.Field()  # 开奖号码
    open_url = scrapy.Field()  # 开奖url
    open_result = scrapy.Field()  # 开奖结果
    create_time = scrapy.Field()  # 创建时间
    update_time = scrapy.Field()  # 更新时间
    source_sn = scrapy.Field()  # 网站标识
    trend_chart = scrapy.Field()  # 走势图
    lottery_result = scrapy.Field()  # 保存标识库


class MetaItemPipeline(object):
    """数据集管道"""

    def __init__(self, crawler):
        name = 'spider_' + crawler.spider.name + '_item'
        # self.mongo = yzwl.db.mongo[name]
        # self.mongo.ensure_index('expect', unique=True)
        self.mysql = db.local_yzwl

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        """保存数据"""
        expect = item.get('expect')
        if not expect:
            raise DropItem("item data type error")
        # self.put_queue(item)
        data = copy.deepcopy(dict(item))
        if not data:
            raise DropItem("item data is empty")

        # info = self.mongo.find_one({'expect': data['expect']})
        lottery_result = item.get('lottery_result', '')
        if not lottery_result:
            raise DropItem("lottery_result is empty")
            # return
        condition = {'expect': expect}
        # mysql 并发造成资源争抢 会造成死锁
        # with lock:
        try:
            info = self.mysql.select(lottery_result, condition=condition, limit=1)
            if not info:
                # self.mongo.insert(data)
                item['create_time'] = util.date()
                item['update_time'] = util.date()
                self.mysql.insert(lottery_result, data=item)
                # _logger.info('success insert mysql : %s' % data['expect'])
            else:
                item['create_time'] = info['create_time']
                item['update_time'] = util.date()
                # self.mongo.update({'_id': info['_id']}, {"$set": data})
                self.mysql.update(lottery_result, condition=condition, data=item)
                # _logger.info('success update mysql : %s' % data['expect'])
        except Exception as e:
            _logger.info('error op mysql : {0}  : e {1}'.format(data['expect'], e))
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


class YzJshSpider(CrawlSpider):
    """jsh365.com 蜘蛛"""
    name = 'jsh365'
    allowed_domains = ['www.jsh365.com', 'https://www.jsh365.com']
    # 类别页面
    start_urls = ['https://www.jsh365.com/award.html']

    def __init__(self, name=None, **kwargs):
        self.mysql = db.local_yzwl
        self.head_url = 'https://www.jsh365.com'
        self._init_args(**kwargs)
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }
        super(YzJshSpider, self).__init__(name, **kwargs)

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
        item = GoodsItem()
        category = resp.xpath('//div[@class="_navList"]//div[contains(@class,"_navItem")]//a//@href').extract()

        for category_url in category:
            if 'gp' in category_url or 'dp' in category_url:
                yield scrapy.Request(url=category_url, headers=self.headers, callback=self.parse_category,
                                     meta={'item': item})

    def parse_category(self, resp):
        '''根据分类页面获取单种类别数据'''
        item = resp.meta.get('item')

        lotto_url = resp.xpath('//table[@class="_tab"]//tr//td[@class="col2"]//a/@href').extract()

        date_list = util.specified_date(self.start_date, end_date=self.end_date)
        for _url in lotto_url:
            # 指定彩种控制
            if self.abbreviation and self.abbreviation not in _url:
                # 非指定的数据不进行抓取(指定彩种的情况下使用该选项)
                continue

            if 'gp-' in _url:
                try:
                    result_key = _url.split('gp-')[-1].split('.html')[0]
                    if result_key == 'bjpks':
                        continue  # 不需要该数据
                    # info = self.mysql.select('t_lottery', condition={'abbreviation': config.JSH_KEY_DICT[result_key]},
                    #                          fields=('lottery_result'), limit=1)
                    lottery_result = config.JSH_KEY_DICT.get(result_key, '')
                except KeyError as e:
                    _logger.info('{0} 网站蜘蛛彩种{1} 错误提示 请人工检查 {2}  e:{3}'.format(self.name, result_key, _url, e))
                    lottery_result = ''

                for history_date in date_list:
                    'https://www.jsh365.com/award/gp-shsyxw/2019-04-24.html'
                    'https://www.jsh365.com/award/gp-shsyxw.html'

                    replace_url_end = '/' + history_date + '.html'  # 获取历史日期拼接成url
                    history_url = _url.replace('.html', replace_url_end)
                    yield Request(url=history_url, headers=self.headers,
                                  callback=self.parse_product,
                                  meta={'item': item, 'history_date': history_date, 'lottery_result': lottery_result})
            elif 'dp-' in _url:
                'https://www.jsh365.com/award/dp-his/shttcxs/500.html'
                'https://www.jsh365.com/award/dp-his/shttcxs.html'
                'https://www.jsh365.com/award/dp-shttcxs.html'
                try:
                    result_key = _url.split('dp-')[-1].split('.html')[0]
                    info = self.mysql.select('t_lottery', condition={'abbreviation': config.JSH_KEY_DICT[result_key]},
                                             fields=('lottery_result'), limit=1)
                    lottery_result = info.get('lottery_result', ) if info else ''
                except KeyError as e:
                    _logger.info('{0} 网站蜘蛛彩种{1} 错误提示 请人工检查 {2}  e: {3}'.format(self.name, result_key, _url, e))
                    lottery_result = ''

                his_url = _url.replace('dp-', 'dp-his/')
                replace_url_end = '/' + '500' + '.html'  # 获取历史的url
                history_url = his_url.replace('.html', replace_url_end)

                yield Request(url=history_url, headers=self.headers,
                              callback=self.parse_product,
                              meta={'item': item, 'history_date': None, 'lottery_result': lottery_result})
            else:
                print('lotto_url11', _url)

    def code_util(self, open_code_list):
        '''开奖号码处理'''
        code_list = []
        for _code in open_code_list:
            code = util.cleartext(_code)
            if code:
                code_list.append(code)
        open_code = ','.join(code_list)

        return open_code

    def parse_product(self, resp):
        '''彩种信息页'''
        item = resp.meta.get('item')
        history_date = resp.meta.get('history_date')
        lottery_result = resp.meta.get('lottery_result')

        item = {
            'expect': '',
            'open_time': '',
            'open_code': '',
            'open_url': '',
            'open_result': '',
            'create_time': '',
            'update_time': '',
            'source_sn': 11,
            'trend_chart': '',
        }
        item['lottery_result'] = lottery_result
        # 获取详情页url

        if 'gp-' in resp.url:
            # 高频彩
            tr_list = resp.xpath('//table[@class="_tab"]//tr')
            for tr in tr_list:
                expect_xpath = tr.xpath('.//td[1]//text()').extract()

                if not expect_xpath:  # 无期号 数据为空
                    continue
                open_time_xpath = tr.xpath('.//td[2]//text()').extract_first()
                open_code_list = tr.xpath('.//td[3]//text()').extract()
                for _expect in expect_xpath:
                    expect = util.cleartext(_expect)
                    if expect:  # 将expect组成一个长度为3的字符串数字 '001-999'
                        if len(expect) == 2:
                            expect = '0' + expect
                        elif len(expect) == 1:
                            expect = '0' + expect
                        else:
                            pass
                        break
                expect = ''.join(history_date.split('-')) + expect
                open_time = history_date + ' ' + util.cleartext(open_time_xpath)

                open_code = self.code_util(open_code_list)

                item['expect'] = util.cleartext(expect, '期')
                item['open_time'] = open_time
                item['open_code'] = open_code
                item['open_url'] = resp.url
                # item['create_time'] = util.date()
                yield item


        elif 'dp-' in resp.url:
            # 地方低频彩
            tr_list = resp.xpath('//table[@rules="all"]//tr')
            for tr in tr_list:
                expect = tr.xpath('.//td[1]//text()').extract_first()
                if not expect:  # 没有获取到期号  数据为空
                    continue
                open_time = tr.xpath('.//td[2]//text()').extract()
                open_code_list = tr.xpath('.//td[3]//text()').extract()
                open_time_list = util.regx_find_num(util.cleartext(open_time[0])) if open_time else []
                open_time = '-'.join(open_time_list)
                open_code = self.code_util(open_code_list)

                item['expect'] = util.cleartext(expect, '期')
                item['open_time'] = open_time
                item['open_code'] = open_code
                item['open_url'] = resp.url
                # item['create_time'] = util.date()
                yield item

        else:
            item = {}
            yield item

    def parse_detail(self, resp):
        '''
        详情页解析  暂无20190425
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
    opt_group.add_argument('-A', '--abbreviation', default=None, help='指定彩种,abbreviation为t_lottery中的 彩票缩写', )

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
