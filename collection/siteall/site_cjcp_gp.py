# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 18:29
# @Author  : TianZe
# @Email   : tianze@86cp.com
# @File    : site_cjcp_gp.py
# @Software: PyCharm
# @Remarks :
import re
import time
import logging
from lxml import etree
from packages import Util, yzwl

session = Util.get_session()
db = yzwl.DbClass()
mysql = db.yzwl
test_mysql = db.test_yzwl
_logger = logging.getLogger('yzwl_spider')


def save_to_db(item, db_name):
    info = mysql.select(db_name, condition=[('expect', '=', item['expect'])], limit=1)
    if not info:
        mysql.insert(db_name, data=item)
        test_mysql.insert(db_name, data=item)
        _logger.info('INFO:  DB:%s 数据保存成功, 期号%s ;' % (db_name, item['expect']))
    else:
        # mysql.update(db_name, condition=[('expect', '=', item['expect'])], data=item)
        _logger.info('INFO:  DB:%s 数据已存在, 期号: %s' % (db_name, item['expect']))


def fetch_data(url, db_name):
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        title = selector.xpath('/html/body/div[1]/article/div/ul/li[1]/div/h1/em[1]/@title')[0]
        expect = selector.xpath('/html/body/div[1]/article/div/ul/li[1]/div/h1/em[2]/text()')[0]
        expect = re.findall(r'第(\d+)期', expect)[0]
        if '快3' in title or title in ['天津快乐十分']:
            expect_list = list(expect)
            del (expect_list[-3])
            expect = ''.join(expect_list)
        date = selector.xpath('/html/body/div[1]/article/div/ul/li[2]/text()')[0]
        open_date = re.findall(r'开奖时间：(.*)$', date)[0]
        codes = selector.xpath('/html/body/div[1]/article/div/ul/li[1]/div/p/span/text()')
        open_code = ','.join(codes)
        cp_id = ''.join(codes)
        open_url = url
        item = {
            'cp_id': cp_id,
            'cp_sn': '25' + expect,
            'expect': expect,
            'open_time': open_date,
            'open_code': open_code,
            'open_url': open_url,
            'create_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        save_to_db(item, db_name)


def get_lottery_list():
    lo_dict = {
        # '北京11选5': 0,
        # '天津11选5': 0,
        '河北11选5': 'game_hebsyxw_result',
        '山西11选5': 'game_shxsyxw_result',
        '内蒙11选5': 'game_nmgsyxw_result',
        '辽宁11选5': 'game_lnsyxw_result',
        '吉林11选5': 'game_jlsyxw_result',
        '黑龙江11选5': 'game_hljsyxw_result',
        '上海11选5': 'game_shsyxw_result',
        '江苏11选5': 'game_jssyxw_result',
        '浙江11选5': 'game_zjsyxw_result',
        '安徽11选5': 'game_ahsyxw_result',
        '江西11选5': 'game_jxsyxw_result',
        # '山东十一运夺金': 0,
        # '河南11选5': 0,
        '湖北11选5': 'game_hbsyxw_result',
        '广东11选5': 'game_gd11x5_result',
        '广西11选5': 'game_gxsyxw_result',
        '贵州11选5': 'game_gzsyxw_result',
        '云南11选5': 'game_ynsyxw_result',
        '陕西11选5': 'game_sxsyxw_result',
        '甘肃11选5': 'game_gssyxw_result',
        '青海11选5': 'game_qhsyxw_result',
        # '宁夏11选5': 0,
        '新疆11选5': 'game_xjsyxw_result',
        # '北京快3': 'game_bjks_result',  # 期号有问题
        '河北快3': 'game_hbks_result',
        '内蒙快3': 'game_nmks_result',
        '吉林快3': 'game_jlks_result',
        '上海快3': 'game_shks_result',
        '江苏快3': 'game_jsks_result',
        '安徽快3': 'game_ahks_result',
        '福建快3': 'game_fjks_result',
        '江西快3': 'game_jxks_result',
        '湖北快3': 'game_hubks_result',
        '广西快3': 'game_gxks_result',
        '贵州快3': 'game_gzks_result',
        '甘肃快3': 'game_gsks_result',
        '青海快3': 'game_qhks_result',
        '天津快乐十分': 'game_tjklsf_result',
        '山西快乐十分': 'game_shxklsf_result',
        '黑龙江快乐十分': 'game_hljklsf_result',
        '湖南动物总动员': 'game_hnklsf_result',
        '广东快乐十分': 'game_gdklsf_result',
        '广西快乐十分': 'game_gxklsf_result',
        '重庆快乐十分': 'game_cqxync_result',
        # '云南快乐十分': 0,
        # '山东快乐扑克3': 'game_sdklpk3_result',
        # '山东群英会': 'game_sdqyh_result',
        # '浙江快乐12': 'game_zjklse_result',
        # '四川12选5': 0,
        # '辽宁快乐12': 'game_lnklse_result',
        # '重庆百变王牌': 0,
        # '山西泳坛夺金': 0,
        '北京快乐8': 'game_bjklb_result',
        '北京Pk10': 'game_pk10_result',
        # '河南泳坛夺金': 'game_hnsby_result',
        # '河南幸运彩': 0,
        '上海时时乐': 'game_shssl_result',
        # '四川金七乐': 0,
        # '湖南幸运赛车': 'game_hnxysc_result',
        # '新疆喜乐彩': 'game_xjxlc_result'
    }
    r = session.get('https://m.cjcp.com.cn/kaijiang/gaopin/')
    if r.status_code == 200:
        content = r.content.decode('utf8')
        selector = etree.HTML(content)
        # 11x5
        x5_list = selector.xpath('//*[@id="syx5start"]/ul/li/a/@href')
        x5_name_list = selector.xpath('//*[@id="syx5start"]/ul/li/a/@title')
        # k3
        k3_list = selector.xpath('//*[@id="ksstart"]/ul/li/a/@href')
        k3_name_list = selector.xpath('//*[@id="ksstart"]/ul/li/a/@title')
        # klsf
        klsf_list = selector.xpath('//*[@id="klsfstart"]/ul/li/a/@href')
        klsf_name_list = selector.xpath('//*[@id="klsfstart"]/ul/li/a/@title')
        # others
        other_list = selector.xpath('//*[@id="gpstart"]/div/div/a/@href')
        other_name_list = selector.xpath('//*[@id="gpstart"]/div/div/a/h1/span[1]/@title')

        all_url_list = x5_list + k3_list + klsf_list + other_list
        all_name_list = x5_name_list + k3_name_list + klsf_name_list + other_name_list
        for url in all_url_list:
            f_url = 'https://m.cjcp.com.cn' + url
            name = all_name_list[all_url_list.index(url)]
            db_name = lo_dict.get(name)
            if db_name:
                fetch_data(f_url, db_name)
                time.sleep(0.5)


def main():
    get_lottery_list()


if __name__ == '__main__':
    main()
