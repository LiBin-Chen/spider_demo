#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import random
import logging
import requests
import argparse
import threading
from lxml import etree

try:
    from packages import yzwl
    from packages import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.yzwl as yzwl
    import packages.Util as util

__author__ = 'snow'
__time__ = '2019/3/16'

_logger = logging.getLogger('yzwl_spider')
_cookies = {'MAINT_NOTIFY_201410': 'notified'}

default_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Cookie': 'UniqueID=KWpJJIaMMbeS4Oi01552741052640; Sites=_21; _ga=GA1.3.166127971.1552205553; _gid=GA1.3.1595082790.1552740249; _gat_gtag_UA_113065506_1=1; 21_vq=46',
    'Host': 'www.cwl.gov.cn',
    'Referer': 'http://www.cwl.gov.cn/kjxx/ssq/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

db = yzwl.DbClass()
mysql = db.yzwl
lock = threading.Lock()


def get_prolist(limit):
    '''
    获取代理列表
    直接从数据库获取，可改为接口获取
    :param limit:
    :return:
    '''
    count = mysql.count('proxies') - limit
    end_number = random.randint(1, count)
    condition = [('pid', '>=', end_number), ('is_pay', '=', 1), ('is_use', '=', 1)]
    data = mysql.select('proxies', condition=condition, limit=limit)
    if isinstance(data, dict):
        return [1, {'ip': data['ip']}]
    dlist = []
    for _data in data:
        # item = {
        #     'ip': _data['ip'],
        # }
        dlist.append(_data['ip'])
    _num = len(dlist)
    return [_num, dlist]


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
        _logger.info('INFO:使用代理, %s ;' % (proxies))

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
    # rs.encoding = 'utf-8'
    rs.encoding = rs.apparent_encoding
    with lock:
        return _parse_detail_data(rs.content, url=url, **kwargs)


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
    root = etree.HTML(data)


def save_data(url, db_name, item, sign=None):
    info = mysql.select(db_name, condition=[('expect', '=', item['expect'])], limit=1)
    if not info:
        mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ; URL:%s' % (db_name, item['expect'], url))

        if sign:
            sys.exit()
    else:
        mysql.update(db_name, condition=[('expect', '=', item['expect'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在 更新成功, 期号: %s ; URL:%s' % (db_name, item['expect'], url))


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


def get_3d_test_code(expect):
    """
        从360彩票获取福彩3D试机号
    :param expect: 期号
    :return: 试机号
    """
    url = 'https://chart.cp.360.cn/kaijiang/sd?lotId=210053&chartType=undefined&spanType=3&span={}_{}'.format(expect,
                                                                                                              expect)
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
    })
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('gbk')
        selector = etree.HTML(content)
        data = selector.xpath('//*[@id="data-tab"]/tr[1]')
        for d in data:
            shijihao = d.xpath('./td[4]/text()')
            test_code = ','.join(list(shijihao[0][:3])) if shijihao else ''
            return test_code
    return ''


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


def api_fetch_data(url=None, proxy=None, **kwargs):
    '''
    从接口获取数据
    '''
    try:
        db_name = kwargs.get('db_name', '')
        if not db_name:
            return
        proxies = kwargs.get('proxies')
        if proxies is None and proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {
                'http': 'http://' + proxy[1][i],
                'https': 'https://' + proxy[1][i]
            }

        if not url:
            return None
        parm_data = {
        }
        try:
            proxies = None
            if isinstance(url, tuple):
                url = url[0]
            res = requests.get(url=url, headers=default_headers, params=parm_data, proxies=proxies)
            res.encoding = res.apparent_encoding
        except requests.RequestException as e:
            print('从接口获取数据失败')
            return -1
        data = res.json()
        result = data['result']
        item_dict = {

        }

        cp_genre = kwargs.get('genre')
        if cp_genre is '1':
            data_item = {"rolling": "0", "bonusSituationDtoList": [
                {"winningConditions": "6+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "一等奖"},
                {"winningConditions": "6+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "二等奖"},
                {"winningConditions": "5+1", "numberOfWinners": "0", "singleNoteBonus": "3000", "prize": "三等奖"},
                {"winningConditions": "5+0,4+1", "numberOfWinners": "0", "singleNoteBonus": "200", "prize": "四等奖"},
                {"winningConditions": "4+0,3+1", "numberOfWinners": "0", "singleNoteBonus": "10", "prize": "五等奖"},
                {"winningConditions": "2+1,1+1,0+1", "numberOfWinners": "0", "singleNoteBonus": "5", "prize": "六等奖"}
            ], "nationalSales": "0", "currentAward": "0"}
        elif cp_genre is '2':
            data_item = {"rolling": "0", "bonusSituationDtoList": [
                {"winningConditions": "与开奖号相同且顺序一致", "numberOfWinners": "0", "singleNoteBonus": "1040", "prize": "直选"},
                {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": "0", "singleNoteBonus": "346", "prize": "组三"},
                {"winningConditions": "与开奖号相同，顺序不限", "numberOfWinners": "0", "singleNoteBonus": "173", "prize": "组六"},
            ], "nationalSales": "0", "currentAward": "0"}
        else:
            data_item = {"rolling": "0", "bonusSituationDtoList": [
                {"winningConditions": "7+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "一等奖"},
                {"winningConditions": "6+1", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "二等奖"},
                {"winningConditions": "6+0", "numberOfWinners": "0", "singleNoteBonus": "0", "prize": "三等奖"},
                {"winningConditions": "5+1", "numberOfWinners": "0", "singleNoteBonus": "200", "prize": "四等奖"},
                {"winningConditions": "5+0", "numberOfWinners": "0", "singleNoteBonus": "50", "prize": "五等奖"},
                {"winningConditions": "4+1", "numberOfWinners": "0", "singleNoteBonus": "10", "prize": "六等奖"},
                {"winningConditions": "4+0", "numberOfWinners": "0", "singleNoteBonus": "5", "prize": "七等奖"},
            ], "nationalSales": "0", "currentAward": "0"}
        index_url = 'http://www.cwl.gov.cn'
        for info in result:
            expect = info['code']
            open_red_code = info['red']
            open_blue_code = info['blue']
            open_date = info['date']
            content = info['content']
            if not content and cp_genre != '2':
                return
            cp_id = open_red_code.replace(',', '') + open_blue_code
            cp_sn = '14' + str(expect)

            details_link = index_url + info['detailsLink']  # http://www.cwl.gov.cn/c/2019-03-14/450353.shtml
            video_link = index_url + info['videoLink']
            prizegrades = info['prizegrades']
            bonusSituationDtoList = data_item['bonusSituationDtoList']
            data_item['rolling'] = util.modify_unit(info['poolmoney'])
            data_item['nationalSales'] = util.modify_unit(info['sales'])

            bonusSituationDtoList[0]['numberOfWinners'] = prizegrades[0]['typenum']
            bonusSituationDtoList[0]['singleNoteBonus'] = prizegrades[0]['typemoney']

            bonusSituationDtoList[1]['numberOfWinners'] = prizegrades[1]['typenum']
            bonusSituationDtoList[1]['singleNoteBonus'] = prizegrades[1]['typemoney']

            bonusSituationDtoList[2]['numberOfWinners'] = prizegrades[2]['typenum']
            bonusSituationDtoList[2]['singleNoteBonus'] = prizegrades[2]['typemoney']

            open_time = open_date.split('(')[0] + ' 21:15:00'
            open_code = open_red_code + open_blue_code  # 3d

            if cp_genre in ['1', '3']:
                open_code = open_red_code + '+' + open_blue_code  # ssq
                bonusSituationDtoList[3]['numberOfWinners'] = prizegrades[3]['typenum']
                bonusSituationDtoList[3]['singleNoteBonus'] = prizegrades[3]['typemoney']

                bonusSituationDtoList[4]['numberOfWinners'] = prizegrades[4]['typenum']
                bonusSituationDtoList[4]['singleNoteBonus'] = prizegrades[4]['typemoney']

                bonusSituationDtoList[5]['numberOfWinners'] = prizegrades[5]['typenum']
                bonusSituationDtoList[5]['singleNoteBonus'] = prizegrades[5]['typemoney']

                if cp_genre in ['3']:
                    open_code = open_red_code + '+' + open_blue_code  # qlc
                    bonusSituationDtoList[5]['numberOfWinners'] = prizegrades[6]['typenum']
                    bonusSituationDtoList[5]['singleNoteBonus'] = prizegrades[6]['typemoney']
            count = 0
            for prize in bonusSituationDtoList:
                if cp_genre != '2':

                    count += util.number_format(prize['numberOfWinners'], places=0) * util.number_format(
                        prize['singleNoteBonus'], places=0)
                else:
                    count += util.number_format(
                        prize['singleNoteBonus'], places=0)

            data_item['currentAward'] = util.modify_unit(count)
            if cp_genre in ['1', '3']:
                item = {
                    'cp_id': cp_id,
                    'cp_sn': cp_sn,
                    'expect': expect,
                    'open_time': open_time,
                    'open_code': open_code,
                    'open_date': open_date,
                    'open_url': '',
                    'open_details_url': details_link,
                    'details_link': details_link,
                    'open_video_url': video_link,
                    'open_content': content,
                    'open_result': json.dumps(data_item, ensure_ascii=True),
                    'create_time': util.date()
                }
                try:
                    sign = kwargs.get('sign', '')
                    save_data(url, db_name, item, sign)
                except Exception as e:
                    _logger.exception('mysql异常： %s' % util.traceback_info(e))
            else:
                # 福彩3d，试机号从360彩票网站获取
                test_code = get_3d_test_code(expect)
                item = {
                    'cp_id': cp_id,
                    'cp_sn': cp_sn,
                    'expect': expect,
                    'open_time': open_time,
                    'open_code': open_code,
                    'test_code': test_code,
                    'open_date': open_date,
                    'open_url': '',
                    'open_details_url': details_link,
                    'details_link': details_link,
                    'open_video_url': video_link,
                    'open_content': content,
                    'open_result': json.dumps(data_item, ensure_ascii=True),
                    'create_time': util.date()
                }
            # print('item', item)
                try:
                    if item['test_code']:
                        sign = kwargs.get('sign', '')
                        save_data(url, db_name, item, sign)
                    else:
                        _logger.info('福彩3D试机号结果未获取，5分钟后重试一次')
                        time.sleep(300)
                        item['test_code'] = get_3d_test_code(item['expect'])
                        if item['test_code']:
                            save_data(url, db_name, item, 1)
                        else:
                            sys.exit()
                except Exception as e:
                    _logger.exception('mysql异常： %s' % util.traceback_info(e))
        return data
    except Exception as e:
        _logger.error('error: %s' % util.traceback_info(e))


def fetch_update_data(url=None, id=None, **kwargs):
    '''
    更新彩票的开奖结果

    @description
        更新数据需要更新,更新赛事的数据
        id
        等等
    '''

    '''
    待开发
    '''
    pass


def main(**kwargs):
    print(kwargs)
    sd = kwargs.get('sd', '')
    ed = kwargs.get('ed', '')
    cp = kwargs.get('cp', '1')
    past = kwargs.get('past', 0)
    sign = kwargs.get('sign', 0)
    interval = kwargs.get('interval', 10)
    _header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    proxy = util.get_prolist(10)
    CP = {
        '1': 'ssq',
        '2': '3d',
        '3': 'qlc',
    }

    RESULT = {
        '1': 'game_ssq_result',
        '2': 'game_sd_result',
        '3': 'game_qlc_result',
    }

    while 1:
        if not past:
            # 下载指定日期的历史数据
            max_page = {
                '1': 10,
                '2': 22,
                '3': 10,
            }
            for _cp in cp:
                if _cp != '2':
                    continue
                for page in range(1, max_page[_cp] + 1):
                    url = 'http://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice?name={0}&issueCount=&issueStart=&issueEnd=&dayStart={1}&dayEnd={2}&pageNo={3}'.format(
                        CP[_cp], sd, ed, page)
                    print('正在请求url: ', url)
                    kwargs['db_name'] = RESULT[_cp]
                    kwargs['genre'] = _cp
                    kwargs['sign'] = sign
                    api_fetch_data(url, proxy, **kwargs)
                    time.sleep(1)  # 按日期获取时每一秒获取一次
        else:
            # 下载指定期数的数据,eg 1 就是下载最新一期,默认500则最近500期
            for _cp in cp:
                url = 'http://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice?name={0}&issueCount={1}'.format(CP[_cp],
                                                                                                           past)

                kwargs['db_name'] = RESULT[_cp]
                kwargs['genre'] = _cp
                api_fetch_data(url, proxy, **kwargs)

        if not interval:
            break
        print('-------------- sleep %s sec -------------' % interval)
        time.sleep(interval)


def cmd():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help=u'获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-p', '--past', help=u'默认最新一期数据',
                        dest='past', action='store', default=0)
    parser.add_argument('-s', '--sign', help=u'定时任务时使用获取到开奖结果即关闭程序的标记',
                        dest='sign', action='store', default=0)
    parser.add_argument('-sd', '--sd', help=u'指定开始下载日期',
                        dest='sd', action='store', default='2010-10-23')
    parser.add_argument('-ed', '--ed', help=u'指定结束下载日期',
                        dest='ed', action='store', default='2019-03-17')
    parser.add_argument('-C', '--cp', help='指定更新彩种(可多选)，不选默认为所有彩种',
                        nargs='+')
    parser.add_argument('-i', '--interval', dest='interval',
                        help='指定暂停时间(默认0)，小于或等于0时则只会执行一次', default=0, type=int)

    args = parser.parse_args()
    if not args.cp:
        args.cp = ['1', '2', '3']
    if args.help:
        parser.print_help()
        print(u"\n示例")
    elif args.past or args.sd:
        main(**args.__dict__)
    else:
        main()


if __name__ == '__main__':
    cmd()
