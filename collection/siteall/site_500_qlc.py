#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'snow'
__time__ = '2019/3/14'

import re
import argparse
import threading
from lxml import etree
import time
import json
import random
import logging
import requests
from packages import Util as util, db, yzwl

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

collection = db.mongo['pay_proxies']
default_headers = {
    'Host': 'kaijiang.500.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
}

db = yzwl.DbClass()
mysql = db.local_yzwl
lock = threading.Lock()

check_list = [
    11144,
    19028,
    19027,
    19026,
    19025,
    19024,
    19023,
    19022,
    19021,
    19020,
    19019,
    19018,
    19017,
    19016,
    19015,
    19014,
    19013,
    19012,
    19011,
    19010,
    19009,
    19008,
    19007,
    19006,
    19005,
    19004,
    19003,
    19002,
    19001,
    18154,
    18153,
    18152,
    18151,
    18150,
    18149,
    18148,
    18147,
    18146,
    18145,
    18144,
    18143,
    18142,
    18141,
    18140,
    18139,
    18138,
    18137,
    18136,
    18135,
    18134,
    18133,
    18132,
    18131,
    18130,
    18129,
    18128,
    18127,
    18126,
    18125,
    18124,
    18123,
    18122,
    18121,
    18120,
    18119,
    18118,
    18117,
    18116,
    18115,
    18114,
    18113,
    18112,
    18111,
    18110,
    18109,
    18108,
    18107,
    18106,
    18105,
    18104,
    18103,
    18102,
    18101,
    18100,
    18099,
    18098,
    18097,
    18096,
    18095,
    18094,
    18093,
    18092,
    18091,
    18090,
    18089,
    18088,
    18087,
    18086,
    18085,
    18084,
    18083,
    18082,
    18081,
    18080,
    18079,
    18078,
    18077,
    18076,
    18075,
    18074,
    18073,
    18072,
    18071,
    18070,
    18069,
    18068,
    18067,
    18066,
    18065,
    18064,
    18063,
    18062,
    18061,
    18060,
    18059,
    18058,
    18057,
    18056,
    18055,
    18054,
    18053,
    18052,
    18051,
    18050,
    18049,
    18048,
    18047,
    18046,
    18045,
    18044,
    18043,
    18042,
    18041,
    18040,
    18039,
    18038,
    18037,
    18036,
    18035,
    18034,
    18033,
    18032,
    18031,
    18030,
    18029,
    18028,
    18027,
    18026,
    18025,
    18024,
    18023,
    18022,
    18021,
    18020,
    18019,
    18018,
    18017,
    18016,
    18015,
    18014,
    18013,
    18012,
    18011,
    18010,
    18009,
    18008,
    18007,
    18006,
    18005,
    18004,
    18003,
    18002,
    18001,
    17153,
    17152,
    17151,
    17150,
    17149,
    17148,
    17147,
    17146,
    17145,
    17144,
    17143,
    17142,
    17141,
    17140,
    17139,
    17138,
    17137,
    17136,
    17135,
    17134,
    17133,
    17132,
    17131,
    17130,
    17129,
    17128,
    17127,
    17126,
    17125,
    17124,
    17123,
    17122,
    17121,
    17120,
    17119,
    17118,
    17117,
    17116,
    17115,
    17114,
    17113,
    17112,
    17111,
    17110,
    17109,
    17108,
    17107,
    17106,
    17105,
    17104,
    17103,
    17102,
    17101,
    17100,
    17099,
    17098,
    17097,
    17096,
    17095,
    17094,
    17093,
    17092,
    17091,
    17090,
    17089,
    17088,
    17087,
    17086,
    17085,
    17084,
    17083,
    17082,
    17081,
    17080,
    17079,
    17078,
    17077,
    17076,
    17075,
    17074,
    17073,
    17072,
    17071,
    17070,
    17069,
    17068,
    17067,
    17066,
    17065,
    17064,
    17063,
    17062,
    17061,
    17060,
    17059,
    17058,
    17057,
    17056,
    17055,
    17054,
    17053,
    17052,
    17051,
    17050,
    17049,
    17048,
    17047,
    17046,
    17045,
    17044,
    17043,
    17042,
    17041,
    17040,
    17039,
    17038,
    17037,
    17036,
    17035,
    17034,
    17033,
    17032,
    17031,
    17030,
    17029,
    17028,
    17027,
    17026,
    17025,
    17024,
    17023,
    17022,
    17021,
    17020,
    17019,
    17018,
    17017,
    17016,
    17015,
    17014,
    17013,
    17012,
    17011,
    17010,
    17009,
    17008,
    17007,
    17006,
    17005,
    17004,
    17003,
    17002,
    17001,
    16154,
    16153,
    16152,
    16151,
    16150,
    16149,
    16148,
    16147,
    16146,
    16145,
    16144,
    16143,
    16142,
    16141,
    16140,
    16139,
    16138,
    16137,
    16136,
    16135,
    16134,
    16133,
    16132,
    16131,
    16130,
    16129,
    16128,
    16127,
    16126,
    16125,
    16124,
    16123,
    16122,
    16121,
    16120,
    16119,
    16118,
    16117,
    16116,
    16115,
    16114,
    16113,
    16112,
    16111,
    16110,
    16109,
    16108,
    16107,
    16106,
    16105,
    16104,
    16103,
    16102,
    16101,
    16100,
    16099,
    16098,
    16097,
    16096,
    16095,
    16094,
    16093,
    16092,
    16091,
    16090,
    16089,
    16088,
    16087,
    16086,
    16085,
    16084,
    16083,
    16082,
    16081,
    16080,
    16079,
    16078,
    16077,
    16076,
    16075,
    16074,
    16073,
    16072,
    16071,
    16070,
    16069,
    16068,
    16067,
    16066,
    16065,
    16064,
    16063,
    16062,
    16061,
    16060,
    16059,
    16058,
    16057,
    16056,
    16055,
    16054,
    16053,
    16052,
    16051,
    16050,
    16049,
    16048,
    16047,
    16046,
    16045,
    16044,
    16043,
    16042,
    16041,
    16040,
    16039,
    16038,
    16037,
    16036,
    16035,
    16034,
    16033,
    16032,
    16031,
    16030,
    16029,
    16028,
    16027,
    16026,
    16025,
    16024,
    16023,
    16022,
    16021,
    16020,
    16019,
    16018,
    16017,
    16016,
    16015,
    16014,
    16013,
    16012,
    16011,
    16010,
    16009,
    16008,
    16007,
    16006,
    16005,
    16004,
    16003,
    16002,
    16001,
    15153,
    15152,
    15151,
    15150,
    15149,
    15148,
    15147,
    15146,
    15145,
    15144,
    15143,
    15142,
    15141,
    15140,
    15139,
    15138,
    15137,
    15136,
    15135,
    15134,
    15133,
    15132,
    15131,
    15130,
    15129,
    15128,
    15127,
    15126,
    15125,
    15124,
    15123,
    15122,
    15121,
    15120,
    15119,
    15118,
    15117,
    15116,
    15115,
    15114,
    15113,
    15112,
    15111,
    15110,
    15109,
    15108,
    15107,
    15106,
    15105,
    15104,
    15103,
    15102,
    15101,
    15100,
    15099,
    15098,
    15097,
    15096,
    15095,
    15094,
    15093,
    15092,
    15091,
    15090,
    15089,
    15088,
    15087,
    15086,
    15085,
    15084,
    15083,
    15082,
    15081,
    15080,
    15079,
    15078,
    15077,
    15076,
    15075,
    15074,
    15073,
    15072,
    15071,
    15070,
    15069,
    15068,
    15067,
    15066,
    15065,
    15064,
    15063,
    15062,
    15061,
    15060,
    15059,
    15058,
    15057,
    15056,
    15055,
    15054,
    15053,
    15052,
    15051,
    15050,
    15049,
    15048,
    15047,
    15046,
    15045,
    15044,
    15043,
    15042,
    15041,
    15040,
    15039,
    15038,
    15037,
    15036,
    15035,
    15034,
    15033,
    15032,
    15031,
    15030,
    15029,
    15028,
    15027,
    15026,
    15025,
    15024,
    15023,
    15022,
    15021,
    15020,
    15019,
    15018,
    15017,
    15016,
    15015,
    15014,
    15013,
    15012,
    15011,
    15010,
    15009,
    15008,
    15007,
    15006,
    15005,
    15004,
    15003,
    15002,
    15001,
    14154,
    14153,
    14152,
    14151,
    14150,
    14149,
    14148,
    14147,
    14146,
    14145,
    14144,
    14143,
    14142,
    14141,
    14140,
    14139,
    14138,
    14137,
    14136,
    14135,
    14134,
    14133,
    14132,
    14131,
    14130,
    14129,
    14128,
    14127,
    14126,
    14125,
    14124,
    14123,
    14122,
    14121,
    14120,
    14119,
    14118,
    14117,
    14116,
    14115,
    14114,
    14113,
    14112,
    14111,
    14110,
    14109,
    14108,
    14107,
    14106,
    14105,
    14104,
    14103,
    14102,
    14101,
    14100,
    14099,
    14098,
    14097,
    14096,
    14095,
    14094,
    14093,
    14092,
    14091,
    14090,
    14089,
    14088,
    14087,
    14086,
    14085,
    14084,
    14083,
    14082,
    14081,
    14080,
    14079,
    14078,
    14077,
    14076,
    14075,
    14074,
    14073,
    14072,
    14071,
    14070,
    14069,
    14068,
    14067,
    14066,
    14065,
    14064,
    14063,
    14062,
    14061,
    14060,
    14059,
    14058,
    14057,
    14056,
    14055,
    14054,
    14053,
    14052,
    14051,
    14050,
    14049,
    14048,
    14047,
    14046,
    14045,
    14044,
    14043,
    14042,
    14041,
    14040,
    14039,
    14038,
    14037,
    14036,
    14035,
    14034,
    14033,
    14032,
    14031,
    14030,
    14029,
    14028,
    14027,
    14026,
    14025,
    14024,
    14023,
    14022,
    14021,
    14020,
    14019,
    14018,
    14017,
    14016,
    14015,
    14014,
    14013,
    14012,
    14011,
    14010,
    14009,
    14008,
    14007,
    14006,
    14005,
    14004,
    14003,
    14002,
    14001,
    13153,
    13152,
    13151,
    13150,
    13149,
    13148,
    13147,
    13146,
    13145,
    13144,
    13143,
    13142,
    13141,
    13140,
    13139,
    13138,
    13137,
    13136,
    13135,
    13134,
    13133,
    13132,
    13131,
    13130,
    13129,
    13128,
    13127,
    13126,
    13125,
    13124,
    13123,
    13122,
    13121,
    13120,
    13119,
    13118,
    13117,
    13116,
    13115,
    13114,
    13113,
    13112,
    13111,
    13110,
    13109,
    13108,
    13107,
    13106,
    13105,
    13104,
    13103,
    13102,
    13101,
    13100,
    13099,
    13098,
    13097,
    13096,
    13095,
    13094,
    13093,
    13092,
    13091,
    13090,
    13089,
    13088,
    13087,
    13086,
    13085,
    13084,
    13083,
    13082,
    13081,
    13080,
    13079,
    13078,
    13077,
    13076,
    13075,
    13074,
    13073,
    13072,
    13071,
    13070,
    13069,
    13068,
    13067,
    13066,
    13065,
    13064,
    13063,
    13062,
    13061,
    13060,
    13059,
    13058,
    13057,
    13056,
    13055,
    13054,
    13053,
    13052,
    13051,
    13050,
    13049,
    13048,
    13047,
    13046,
    13045,
    13044,
    13043,
    13042,
    13041,
    13040,
    13039,
    13038,
    13037,
    13036,
    13035,
    13034,
    13033,
    13032,
    13031,
    13030,
    13029,
    13028,
    13027,
    13026,
    13025,
    13024,
    13023,
    13022,
    13021,
    13020,
    13019,
    13018,
    13017,
    13016,
    13015,
    13014,
    13013,
    13012,
    13011,
    13010,
    13009,
    13008,
    13007,
    13006,
    13005,
    13004,
    13003,
    13002,
    13001,
    12154,
    12153,
    12152,
    12151,
    12150,
    12149,
    12148,
    12147,
    12146,
    12145,
    12144,
    12143,
    12142,
    12141,
    12140,
    12139,
    12138,
    12137,
    12136,
    12135,
    12134,
    12133,
    12132,
    12131,
    12130,
    12129,
    12128,
    12127,
    12126,
    12125,
    12124,
    12123,
    12122,
    12121,
    12120,
    12119,
    12118,
    12117,
    12116,
    12115,
    12114,
    12113,
    12112,
    12111,
    12110,
    12109,
    12108,
    12107,
    12106,
    12105,
    12104,
    12103,
    12102,
    12101,
    12100,
    12099,
    12098,
    12097,
    12096,
    12095,
    12094,
    12093,
    12092,
    12091,
    12090,
    12089,
    12088,
    12087,
    12086,
    12085,
    12084,
    12083,
    12082,
    12081,
    12080,
    12079,
    12078,
    12077,
    12076,
    12075,
    12074,
    12073,
    12072,
    12071,
    12070,
    12069,
    12068,
    12067,
    12066,
    12065,
    12064,
    12063,
    12062,
    12061,
    12060,
    12059,
    12058,
    12057,
    12056,
    12055,
    12054,
    12053,
    12052,
    12051,
    12050,
    12049,
    12048,
    12047,
    12046,
    12045,
    12044,
    12043,
    12042,
    12041,
    12040,
    12039,
    12038,
    12037,
    12036,
    12035,
    12034,
    12033,
    12032,
    12031,
    12030,
    12029,
    12028,
    12027,
    12026,
    12025,
    12024,
    12023,
    12022,
    12021,
    12020,
    12019,
    12018,
    12017,
    12016,
    12015,
    12014,
    12013,
    12012,
    12011,
    12010,
    12009,
    12008,
    12007,
    12006,
    12005,
    12004,
    12003,
    12002,
    12001,
    11153,
    11152,
    11151,
    11150,
    11149,
    11148,
    11147,
    11146,
    11145,
]


def get_prolist(limit=10):
    """
    获取代理列表
    从url获取改为从数据库获取
    """
    res = requests.get('http://localhost:8888/api/p/proxy/nTAZhs5QxjCNwiZ61/{0}/pay'.format(limit))
    data = res.json()
    # data = collection.find({}).limit(limit)
    prolist = []
    for vo in data:
        prolist.append(vo['ip'])
    _num = len(prolist)
    if _num <= 1:
        return None
    # print(_num, prolist)
    return [_num, prolist]


# prolist = []
# data = collection.find({}).limit(limit)
# for vo in data:
#     prolist.append(vo['ip'])
# _num = len(prolist)
# if _num <= 1:
#     return None
# # print(_num, prolist)
# return [_num, prolist]


def fetch_data(url, proxy=None, headers=None, **kwargs):
    '''
    获取页面数据
    @description
        获取体育赛事数据


    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据
    '''

    if isinstance(headers, dict):
        default_headers = headers
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}

        sess = requests.Session()
        # _logger.info('INFO:使用代理, %s ;' % (proxies))

        print('获取url： {0}'.format(url))
        rs = sess.get(url, headers=default_headers, cookies=_cookies, timeout=30, proxies=None)
        # print('rs', rs.text)

    except Exception as e:
        # 将进行重试，可忽略
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    if rs.status_code != 200:
        if rs.status_code == 500 and 'Thank you for dropping by' in rs.text:
            _logger.debug('STATUS:-500 ; INFO:请求被禁止 ; PROXY：%s ; URL:%s ; User-Agent:%s' % (
                proxies['http'] if proxy else '', url, headers.get('user_agent', '')))
            return -500
        # 已失效产品（url不存在）
        elif rs.status_code == 404:

            _logger.debug('STATUS:404 ; INFO:请求错误 ; URL:%s' % url)
            return 404
        _logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            rs.status_code, proxies['http'] if proxy else '', url))
        return -405
    # 强制utf-8
    rs.encoding = rs.apparent_encoding
    # print('kwargs', kwargs)
    with lock:
        return _parse_detail_data(rs.text, url=url, **kwargs)


# print('t', t)


def _parse_detail_data(data=None, url=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    data_item = {}
    db_name = kwargs.get('db_name', '')

    if not db_name:
        _logger.info('INFO: 请检查是否传入正确的数据库; URL:%s' % (url))
        return
    if not data:
        _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        return -404
    # print('data', data)
    root = etree.HTML(data)
    open_xpath = root.xpath('//div[@class="ball_box01"]//text()')
    code_list = []
    for _code in open_xpath:
        _code = util.cleartext(_code)
        if not _code:
            continue
        code_list.append(_code)
    open_code = ','.join(code_list)
    roll = root.xpath('//span[@class="cfont1 "]//text()')

    # print('currentAward',currentAward)
    # print('rool', roll)
    roll = util.cleartext(roll[1])
    currentAward = util.cleartext(roll[0])

    expect_path = root.xpath('//font[@class="cfont2"]//text()')
    expect = '20' + util.cleartext(expect_path[0])
    date_xpath = root.xpath('//span[@class="span_right"]//text()')
    open_date = date_xpath[0].split(' ')[0].split('开奖日期：')[-1]

    year = open_date.split('年')[0]
    mon = open_date.split('年')[-1].split('月')[0]
    day = open_date.split('年')[-1].split('月')[-1].replace('日', '')
    mon = '0' + mon if len(mon) == 1 else mon
    day = '0' + day if len(day) == 1 else day

    open_time = year + '-' + mon + '-' + day + ' ' + '00:00:00'
    tr_list = root.xpath('//table[@class="kj_tablelist02"]//tr[@align="center"]')

    data_item = {"rolling": "0", "bonusSituationDtoList": [
        {"winningConditions": "7+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "一等奖"},
        {"winningConditions": "6+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "二等奖"},
        {"winningConditions": "6+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "三等奖"},
        {"winningConditions": "5+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "四等奖"},
        {"winningConditions": "5+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "五等奖"},
        {"winningConditions": "4+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "六等奖"},
        {"prize": "七等奖"}], "nationalSales": "0万"}
    data_item['currentAward'] = currentAward
    data_item['nationalSales'] = 0
    # data_item['currentAward'] = currentAward
    for tr in tr_list[2:9]:
        prize_name = tr.xpath('.//td[1]//text()')  # 2 3
        prize_number = tr.xpath('.//td[2]//text()')
        prize = tr.xpath('.//td[3]//text()')
        prize_name = [util.cleartext(prize_name[0])]
        prize = [util.cleartext(prize[0])]
        prize_number = [util.cleartext(prize_number[0])]
        # print(prize_name)
        # print(prize)
        # print(prize_number)

        if prize_name == ['一等奖']:
            data_item['bonusSituationDtoList'][0]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][0]['singleNoteBonus'] = prize[0]
        elif prize_name == ['二等奖']:
            data_item['bonusSituationDtoList'][1]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][1]['singleNoteBonus'] = prize[0]
        elif prize_name == ['三等奖']:
            data_item['bonusSituationDtoList'][2]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][2]['singleNoteBonus'] = prize[0]
        elif prize_name == ['四等奖']:
            data_item['bonusSituationDtoList'][3]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][3]['singleNoteBonus'] = prize[0]
        elif prize_name == ['五等奖']:
            data_item['bonusSituationDtoList'][4]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][4]['singleNoteBonus'] = prize[0]
        elif prize_name == ['六等奖']:
            data_item['bonusSituationDtoList'][5]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][5]['singleNoteBonus'] = prize[0]
        elif prize_name == ['七等奖']:
            data_item['bonusSituationDtoList'][6]['numberOfWinners'] = prize_number[0]
            data_item['bonusSituationDtoList'][6]['singleNoteBonus'] = prize[0]

    data_item = json.dumps(data_item, ensure_ascii=True)
    item = {
        'open_result': data_item,
        'open_time': open_time,
    }

    # print('item', item)
    # print('item', open_code)
    # print('item', expect)
    # print('不保存数据')
    # try:
    #     save_data(url, db_name, open_code, expect, item)
    # except:
    #     _logger.info('INFO: 数据存入错误; item: {0}'.format(item))


def parse_list(bonusSituationDtoList, data_list):
    if not data_list:
        return
    # print('data_list', data_list)
    item = {
    }
    print('dlist', data_list)
    try:
        numberOfWinners = data_list[2] if len(data_list) >= 2 else 0
        singleNoteBonus = data_list[3] if len(data_list) >= 3 else 0
    except:
        numberOfWinners = 0
        singleNoteBonus = 0
    item['numberOfWinners'] = numberOfWinners
    item['singleNoteBonus'] = singleNoteBonus
    if '追加' in data_list:
        try:
            item['additionNumber'] = data_list[6] if len(data_list) >= 6 else 0
            item['additionBonus'] = data_list[7] if len(data_list) >= 7 else 0
        except:
            item['additionNumber'] = 0
            item['additionBonus'] = 0
    bonusSituationDtoList.append(item)


def parse_data(data, symol=1):
    data_list = []

    for _data in data:
        if symol == 1:
            _data = util.cleartext(_data)
        else:
            _data = int(util.number_format(util.cleartext(_data)))
        data_list.append(_data)

    return data_list


def save_data(url, db_name, open_code, expect, item):
    # print('item', item)
    # print('db_name', db_name)
    info = mysql.select(db_name, condition=[('expect', '=', expect)], limit=1)
    if not info:
        cp_id = open_code.replace(',', '')
        item['cp_id'] = cp_id
        item['cp_sn'] = expect
        item['open_url'] = url
        item['open_code'] = open_code
        item['expect'] = expect
        item['create_time'] = util.date()
        print('item', item)
        mysql.insert(db_name, data=item)
        _logger.info('INFO:数据保存成功, 期号%s ; URL:%s' % (expect, url))
    else:
        mysql.update(db_name, condition=[('expect', '=', expect)], data=item)
    _logger.info('INFO:数据已存在 作更新, 期号: %s ; URL:%s' % (expect, url))


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    '''
    根据关键词抓取搜索数据
    '''
    if keyword:
        print('正在获取关键词：%s 的相关数据' % keyword)
        keyword = keyword.replace('*', '')
        url = ''
    elif 'url' in kwargs:
        url = kwargs['url']
    else:
        return

    try:
        proxies = None
        if proxy:
            proxies = {'http': 'http://{0}'.format(random.choice(proxy[1]))}
        rs = requests.get(url, headers=default_headers, cookies=_cookies, timeout=20, proxies=proxies)
    except Exception as e:
        _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        if 'Invalid URL' not in str(e):
            data_dict['list'].append({'status': -400, 'url': url, 'id': id, 'count': kwargs.get('count', 1)})
        return -400

    if rs.status_code not in (200, 301, 302):
        if rs.status_code == 500 and 'Thank you for dropping by' in rs.text:
            _logger.debug('STATUS:-500 ; INFO:请求被禁止 ; PROXY：%s ; URL:%s ; User-Agent:%s' % (
                proxies['http'] if proxy else '', url, headers.get('user_agent', '')))
            data_dict['url'].append({'status': -500, 'url': url, 'id': id})
            return -500
        _logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            rs.status_code, proxies['http'] if proxy else '', url))
        data_dict['list'].append({'status': -405, 'url': url, 'id': id, 'count': kwargs.get('count', 1)})
        return -405

    # 强制utf-8
    rs.encoding = 'utf-8'
    return 200


def fetch_search_list(url, id=None, headers=None, proxy=None, **kwargs):
    '''
    抓取搜索列表数据
    '''
    data_dict = {
        'detail': [],
        'list': [],
        'url': []
    }
    fetch_search_data(id=id, data_dict=data_dict, headers=headers, proxy=proxy, url=url, **kwargs)
    return data_dict


def api_fetch_data(goods_sn=None, keyword=None, proxy=None, numofresult=1, **kwargs):
    '''
    从接口获取数据
    '''
    proxies = kwargs.get('proxies')
    if proxies is None and proxy:
        i = random.randint(0, proxy[0] - 1)
        proxies = {
            'http': 'http://' + proxy[1][i],
            'https': 'http://' + proxy[1][i]
        }

    api_url = ''
    if not api_url:
        return None

    parm_data = {
    }
    sess = requests.Session()
    headers = default_headers.copy()
    headers['Host'] = ''
    try:
        res = sess.get(url=api_url, headers=headers, params=parm_data, proxies=proxies)
    except requests.RequestException as e:
        print('从接口获取数据失败')
        return -1
    data = json.loads(res.content)
    '''
    接口数据解析
    '''
    return data


def fetch_update_data(url=None, id=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''
    headers = kwargs.get('headers')
    proxy = kwargs.get('proxy')
    expect = kwargs.get('expect')  # 最新的期数
    open_time = kwargs.get('open_time')  # 最新的开奖时间，如果是第一期，则由上期作为识别
    open_url = kwargs.get('open_url')  # 同上
    provider_name = kwargs.get('provider_name')
    hot_update = kwargs.get('hot_update', False)
    kw = kwargs.get('kw', '')
    return


def run(url, proxy, **kwargs):
    if url:
        result = fetch_data(url=url, proxy=proxy, headers=default_headers, **kwargs)


def main(**kwargs):
    max_thread = 10
    task_list = []
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    interval = kwargs.get('interval', 10)
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    # data = mysql.select('t_lottery',
    #                     fields=('abbreviation', 'lottery_name', 'lottery_type', 'lottery_result', 'jsh_open_url',
    #                             ))
    # if not data:
    #     print('没有获取到数据')
    #     return
    # proxy = get_prolist(20)
    proxy = None

    CP = {
        # 93: 'http://kaijiang.500.com/shtml/dlt/07002.shtml',  #
        # 93: 'http://kaijiang.500.com/shtml/dlt/14052.shtml',  # 14052后 就是改版后的页面
        93: 'http://kaijiang.500.com/shtml/qlc/12007.shtml',  # 14052后 就是改版后的页面
        # 93: 'http://kaijiang.500.com/shtml/dlt/19028.shtml',  # 14052后 就是改版后的页面
    }
    RESULT = {
        93: 'game_qlc_result',
    }
    url = CP[93]
    while 1:
        lottery_result = RESULT[93]
        kwargs['db_name'] = lottery_result
        expect = url.split('/')[-1].split('.')[0]
        new_expect = int(expect)
        if new_expect not in check_list:
            # print('ne',new_expect)
            print('不存在该期数据： ', new_expect)
        else:
            run(url, proxy, **kwargs)
            time.sleep(5)
        # run(url, proxy, **kwargs)
        # expect = url.split('/')[-1].split('.')[0]
        # new_expect = int(expect)
        new_expect += 1
        if len(str(new_expect)) < len(expect):
            new_expect = '0' + str(new_expect)
        if int(new_expect) > 19025:
            break
        url = url.replace(expect, str(new_expect))
        print('url', url)
        # break

        # lottery_result = RESULT[key]
        # # info = mysql.select(lottery_result,
        # #                     fields=('open_time',), order='open_time desc', limit=1)
        # # t = threading.Thread(target=run, args=(interval, info, proxy, _data, dlist), kwargs=kwargs,
        # #                      name='thread-{0}'.format(len(task_list)))
        # kwargs['url_type'] = key
        # kwargs['db_name'] = lottery_result
        #
        # run(url, proxy, **kwargs)
        # # break


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    # parser.add_argument('-u', '--url', help=u'从检索结果的 URL 开始遍历下载产品数据',
    #                     dest='url', action='store', default=None)
    parser.add_argument('-sd', '--sd', help=u'从指定日期开始下载数据',
                        dest='sd', action='store', default='03/01/2019')
    parser.add_argument('-ed', '--ed', help=u'从指定日期结束下载数据',
                        dest='ed', action='store', default=None)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    if args.help:
        parser.print_help()
        # print(u"\n示例")
    elif args.sd:
        main(**args.__dict__)
    else:
        main()


if __name__ == '__main__':
    cmd()
    # while 1:
    #     cmd()
    # time.sleep(60)
