#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    爱奇艺请求登录
'''
import logging

import execjs
import requests
from lxml import etree

from packages import Util as util

_logger = logging.getLogger('demo_spider')

DEFAULT_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36', }


class Login():

    def __init__(self, url, method, js_file, js_fun, username, password, form_data, headers):
        self.url = url
        self.method = method
        self.js_file = js_file
        self.js_fun = js_fun
        self.username = username
        self.password = password
        self.form_data = form_data
        self.headers = headers

    def run_js(self):
        '''
        调用js文件中的函数,返回js执行的值
        :param js_fun_name:
        :param kwargs:
        :return:
        '''

        js_str = self.load_js()
        ctx = execjs.compile(js_str)  # 加载JS文件
        encryption_str = ctx.call(self.js_fun, self.password)  # 调用js方法  第一个参数是JS的方法名，后面的data和key是js方法的参数

        self.form_data['email'] = self.username
        self.form_data['passwd'] = encryption_str

    def load_js(self):
        '''
        加载js文件
        :return:
        '''
        file_path = util.get_static_file(self.js_file)
        #
        try:
            with open(file_path, 'r', encoding='utf-8') as fp:
                js_str = fp.read()
        except Exception as e:
            _logger.info('INFO: 加载js文件错误 {0}'.format(util.traceback_info(e)))
            js_str = ''

        return js_str

    def fetch_data(self):
        '''
        获取页面数据
        '''
        headers = self.headers if self.headers else DEFAULT_HEADER

        try:
            sess = requests.Session()
            print('获取url： {0}'.format(self.url))

            if self.method == 'GET':
                rs = sess.get(self.url, headers=headers, cookies=None, timeout=30, proxies=None)
            elif self.method == 'POST':
                rs = sess.post(self.url, data=self.form_data, headers=headers, cookies=None, timeout=30,
                               proxies=None)
            else:
                _logger.info('INFO:请求方法未定义 ; URL: {0}'.format(self.url))
            print('rs', rs)
            print(rs.text, rs.text)
        except Exception as e:
            # 将进行重试，可忽略
            _logger.info('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), self.url))
            return -400

        if rs.status_code != 200:
            if rs.status_code == 404:
                _logger.debug('STATUS:404 ; INFO:请求错误 ; URL:%s' % self.url)
                return 404

        # 强制utf-8
        # rs.encoding = 'utf-8'
        rs.encoding = rs.apparent_encoding
        return self._parse_detail_data(rs.content)

    def _parse_detail_data(self, data=None):
        '''
        解析详情数据，独立出来

        data    页面数据
        url     解析的页面url（方便记录异常）
        kwargs  扩展参数
        '''
        if not data:
            _logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % self.url)
            return -404
        root = etree.HTML(data)


if __name__ == '__main__':
    login_url = 'https://passport.iqiyi.com/apis/reglogin/login.action'
    form_data = {
        'fromSDK': 1,
        'sdk_version': '1.0.0',
        'agenttype': 1,
        '__NEW': 1,
        'checkExist': 1,
        'lang': '',
        # 'ptid': '01010021010000000000',
        'nr': 1,
        'verifyPhone': 1,
        # 'area_code': 86,
        # 'dfp': 'a08912e7eef2704975a03513ba0a5de35dab16aac603d354d6de3a0fbe19cece6e',
    }
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.iqiyi.com',
        'Referer': 'https://www.iqiyi.com/iframe/loginreg?ver=1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
    }
    method = 'POST'
    username = ''
    password = ''
    js_file = 'iqiyi.js'
    js_fun = 'getpwd'
    _login = Login(login_url, method, js_file, js_fun, username, password, form_data, headers)

    _login.run_js()
    _login.fetch_data()
