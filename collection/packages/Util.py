#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
  @desc    :
  @time    : 2018/11/28 15:27
  @file    : Util.py
  @author  : snow
  @modify  :
'''

import logging
import math
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re, sys, time, datetime, locale, traceback, subprocess, os, signal, smtplib, urllib
import pandas as pd
import requests
from numpy import unicode

# from packages import db
from packages import yzwl

try:
    import zlkg.config as config
except ImportError:
    pass

try:
    import json
except ImportError:
    import simplejson as json

'''
工具函数，封装常用操作
'''


# mysql = db.yzwl


def date(timestamp=None, format='%Y-%m-%d %H:%M:%S'):
    '''
    时间戳格式化转换日期

    @params
            timestamp ：时间戳，如果为空则显示当前时间
            format : 时间格式

        @return
            返回格式化的时间，默认为 2014-07-30 09:50 这样的形式
        '''
    if timestamp is None:
        timestamp = int(time.time())
    if not isinstance(timestamp, int):
        timestamp = int(timestamp)
    d = datetime.datetime.fromtimestamp(timestamp)
    return d.strftime(format)


def strtotime(string, format="%Y-%m-%d %H:%M"):
    '''
    字符串转时间戳

    @params
        string : 需要转换成时间戳的字符串，需要与后面的format对应
        format : 时间格式

    @return
        返回对应的10位int数值的时间戳
    '''
    try:
        return int(time.mktime(time.strptime(string, format)))
    except Exception as e:
        print('e',e)
        return 0


def filter_symbols(text):
    '''
    剔除数字，字母，汉字以外的字符
    :param text:
    :return:
    '''
    rule = re.compile(r"[^a-zA-Z0-9\u4e00-\u9fa5]")
    text = rule.sub('', text)
    return text


def cleartext(text, *args, **kwargs):
    '''
    过滤特殊字符，获取纯文本字符串，默认过滤换行符 \n、\r、\t 以及多余的空格

    @params
        args : 为添加需要为过滤的字符

    @return
        返回过滤后的字符串，如果为非字符串类型则会被转换成字符串再过滤
    '''
    if isinstance(text, bytes):
        text = text.encode('utf-8')
    elif not isinstance(text, str):
        text = str(text)
    text = text.replace("\r", '')
    text = text.replace("\n", '')
    text = text.replace("\t", '')
    text = text.rstrip()
    text = text.lstrip()
    for arg in args:
        text = text.replace(arg, '')
    return text


def addslashes(text):
    '''
    使用反斜线转义字符串中的字符

    @params
        text : 需要转义的字符串

    @return
        返回转义的字符串
    '''
    if not isinstance(text, str):
        text = str(text)
    l = ["\\", '"', "'", "\0"]
    for i in l:
        if i in text:
            text = text.replace(i, '\\' + i)
    return text


_number_regex = None


def number_format(num, places=5, index=0, smart=False):
    '''
    格式化数值

    @params
        num     可为任意数值，如果为 'kk12.3dsd' 则实际num将为 12.3; asas126.36.356sa => 126.36
        places  小数点后位数，默认为5，如果为0或者负数则返回整数值
        index   索引值，即匹配的第几个数值 - 1,除非你清楚匹配的索引值，否则建议默认
        smart   智能匹配，如果为True'时即当index无法匹配时，智能匹配至与index最近的一个，
                选择False当不匹配时会抛出异常；选择None则会匹配最小的情况
    @return
        格式化的float值或者int值
    '''
    global _number_regex
    if not isinstance(num, (int, float)):
        if _number_regex is None:
            _number_regex = re.compile('(\-{0,1}\d*\.{0,1}\d+)')
        num = cleartext(num).replace(',', '')
        match = _number_regex.findall(num)
        try:
            num = float(match[index]) if match else 0.0
        except Exception as e:
            if smart is None:
                num = match[0]
            elif smart:
                num = float(match[len(match) - 1])
            else:
                raise Exception(str(e))
    if places > 0:
        return float(locale.format("%.*f", (places, float(num)), True))
    else:
        return int(num)


def traceback_info(e=None, return_all=False):
    '''
    获取traceback信息
    '''
    try:
        _info = sys.exc_info()
        if return_all:
            etb_list = traceback.extract_tb(_info[2])
            _trace_info = "Traceback (most recent call last):\n"
            for etb in etb_list:
                _trace_info += "  File: \"%s\" ,line %s, in %s\n      %s\n" % (etb[0], etb[1], etb[2], etb[3])
            _trace_info += '%s : %s' % (_info[1].__class__.__name__, _info[1])
            return _trace_info
        else:
            etb = traceback.extract_tb(_info[2])[0]
            return '<traceback: %s ,line %s, %s ; message: %s>' % (etb[0], etb[1], etb[3], _info[1])
    except Exception:
        return str(e) if e else None


def open_subprocess(cmd, obstruct=True):
    '''
    启动一个新的子进程

    @param cmd      命令
    @param obstruct 阻塞式，默认为true，阻塞式将重定向子进程的输出信息至缓冲区（如希望子进程后台运行不显示信息）

    '''
    if not obstruct:
        if os.name == 'nt':
            process = subprocess.Popen(cmd, shell=True)
        else:
            process = subprocess.Popen(cmd, shell=True)
    else:
        if os.name == 'nt':
            process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        else:
            process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, preexec_fn=os.setsid,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def kill_subprocess(process):
    '''
    结束一子进程
    '''
    if process is None:
        return
    try:
        if os.name == 'nt':
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait()
    except Exception:
        pass


def filemtime(path, root_path=None):
    '''
    取得文件修改的时间
    '''
    FILE_PATH = os.path.join(root_path, path) if root_path else path
    return os.stat(FILE_PATH).st_mtime


def filectime(path, root_path=None):
    '''
    取得文件创建的时间
    '''
    FILE_PATH = os.path.join(root_path, path) if root_path else path
    return os.stat(FILE_PATH).st_ctime


def decorator_except_sendemail(text):
    """
    异常邮件通知装饰器
    :param text:
    :return:
    """

    def decorator(func):
        def wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as e:
                _except_notice = {
                    'OperationalError': '数据库操作错误',
                    'UnicodeDecodeError': '程序编码错误',
                    'TypeError': '程序操作类型错误',
                    'InternalError': '数据库内部错误',
                }
                _except_class_name = e.__class__.__name__
                except_msg = e
                if not _except_class_name:
                    _except_class_name = 'UnknowError'
                except_name = _except_notice.get(_except_class_name, _except_class_name)
                except_msg = traceback_info(except_msg, return_all=1)
                subject = '%s %s' % (text, date(),)
                content = '程序已终止，异常类型：%s，异常详情：%s' % (except_name, except_msg)
                sendmail(config.EMAIL_NOTICE['accept_list'], subject, content)
                _logger = logging.getLogger('yzwl_spider')
                _logger.exception('程序异常终止')

        return wrapper

    return decorator


def sendmail(to_email, subject=None, body=None, attachment=None, **kwargs):
    '''
    发送邮件

    @param to_email     发送对方邮件，可为列表、字符串、元祖
    @param subject      邮件主题，默认为 system@hqchip.com
    @param body         邮件内容
    @param attachment   附件
        支持直接字符串路径 '/var/usr/file' 或者多个附件 ['/var/usr/file1','/var/usr/file2']
        及重命名式的 ('附件','/var/usr/file') 或者 [('附件1','/var/usr/file1'),('附件2','/var/usr/file2')]
        抑或 ('附件1',open('/var/usr/file1','rb'))
    @param kwargs       邮件配置
        SMTP_HOST       smtp服务器地址，域名(不带http)或者ip地址
        SMTP_PORT       smtp服务器端口，默认为25
        SMTP_USER       smtp登陆账号
        SMTP_PASSWORD   smtp登陆密码
        SMTP_FROM       smtp发信来源，部分邮箱检测较为严格，如果与SMTP_USER不一致可能被判为垃圾邮件或者拒绝接收
        SMTP_DEBUG      smtp DEBUG默认为True,True将打印debug信息

    @return 成功返回 True 失败返回 异常信息
    '''
    if not to_email:
        return
    try:
        kwargs.update(config.EMAIL)
    except Exception:
        pass
    if attachment is None:
        attachment = []
    if body is None:
        body = ''

    if not isinstance(to_email, (list, tuple)):
        to_email = [to_email]

    # 创建一个带附件的实例
    msg = MIMEMultipart()
    # 添加邮件头部信息
    msg['From'] = kwargs.get('SMTP_FROM', 'system@hqchip.com')
    msg['To'] = ','.join(to_email)
    msg['Subject'] = 'FROM : %s' % kwargs.get('SMTP_FROM', 'system@hqchip.com') if subject is None else subject
    msg['Date'] = time.ctime(time.time())
    msg.attach(MIMEText(body, 'html', 'utf-8'))

    # 处理附件
    if not isinstance(attachment, list):
        attachment = [attachment]

    for attach in attachment:
        fp = None
        if isinstance(attach, (tuple, list)):
            if isinstance(attach[1], file):
                fp = attach[1]
            elif os.path.exists(attach[1]):
                fp = open(attach[1], 'rb')
            fn = attach[0]
        elif os.path.exists(attach):
            fn = os.path.basename(attach)
            fp = open(attach, 'rb')
        if not fp:
            continue
        att = MIMEText(fp.read(), 'base64', 'utf-8')
        fp.close()
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="%s"' % fn
        msg.attach(att)

    try:
        smtp = smtplib.SMTP()
        smtp.set_debuglevel(kwargs.get('SMTP_DEBUG', False))
        smtp.connect(kwargs.get('SMTP_HOST'), kwargs.get('SMTP_PORT', 25))
        smtp.starttls()
        smtp.login(kwargs.get('SMTP_USER'), kwargs.get('SMTP_PASSWORD'))
        smtp.sendmail(kwargs.get('SMTP_FROM', 'system@hqchip.com'), to_email, msg.as_string())
        smtp.close()

        return True
    except Exception as e:
        if kwargs.get('SMTP_DEBUG', False):
            logging.exception('STATUS:215 ; INFO:%s' % traceback_info(e))
        return False


def file(name='', value='', path='', _cache={}):
    '''
    快速存取文件内容
    '''
    if not name:
        return None
    filepath = os.path.join(config.APP_ROOT, 'database', path, name)
    if value != '':
        if value is None:
            try:
                os.unlink(filepath)
                del _cache[name]
                return True
            except Exception:
                return False
        else:
            dirpath = os.path.dirname(filepath)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            _cache[name] = value
            fp = open(filepath, 'w+')
            fp.write(json.dumps(value))
            fp.close()
            return True

    if name in _cache:
        return _cache[name]

    if os.path.isfile(filepath):
        fp = open(filepath, 'r+')
        try:
            value = json.loads(fp.read())
        except ValueError:
            value = None
        fp.close()
        if value:
            _cache[name] = value
    else:
        value = None
    return value


def urlencode(s):
    return urllib.quote_plus(s)


def urldecode(s):
    return urllib.unquote_plus(s)


def parse_str(qs):
    '''
    解析字符串
    >例如 qs => http://xxx.com?m[]=1&m[]=2&action=search&id=11 解析结果为 {'m':['1','2'],'action':'search','id':'11'}
    '''
    qs = qs.split('?')[-1]
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        if not name_value:
            continue
        nv = name_value.split('=', 1)
        if len(nv[1]):
            name = urldecode(nv[0])
            value = urldecode(nv[1])
            r.append((name, value))
    str_dict = {}
    for name, value in r:
        if name in str_dict:
            str_dict[name].append(value)
        elif name[-2:] == '[]':
            name = name[:-2]
            if not name:
                continue
            str_dict[name] = [value]
        else:
            str_dict[name] = value
    return str_dict


_strip_regex = None
_smart_strip_regex = None


def get_host(url):
    """
    对于给定的url，返回其协议 scheme，主机名 host和 端口 port，如果没有这些则会返回None

    示例：

        >>> get_host('http://google.com/mail/')
        ('http', 'google.com', None)
        >>> get_host('google.com:80')
        ('http', 'google.com', 80)
    """
    port = None
    scheme = 'http'
    if '://' in url:
        scheme, url = url.split('://', 1)
    if '/' in url:
        url, _path = url.split('/', 1)
    if '@' in url:
        _auth, url = url.split('@', 1)
    if ':' in url:
        url, port = url.split(':', 1)
        if not port.isdigit():
            raise Exception("Failed to parse: %s")
        port = int(port)
    return scheme, url, port


def get_local_ip(ifname='eth0'):
    '''
    获取本地ip地址
    :param ifname:      网卡名称，仅对unix or linux系统有效
    :return:
    '''
    import socket
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = '127.0.0.1'
        if os.name != 'nt':
            import fcntl, struct
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])
    return ip


def str_to_unicode(data):
    """字符串转unicode字符串"""
    if not isinstance(data, str):
        return data
    return data.decode('utf-8')


def get_time_desc(t):
    '''
    获取时间描述
    :param t:
    :return:
    '''
    _time_desc = ''
    h = int(t / 3600)
    if h >= 1:
        _time_desc += '%s 小时' % h
    m = int((t - h * 3600) / 60)
    if m >= 1:
        _time_desc += '%s 分' % m
    s = number_format(t - h * 3600 - m * 60, 3)
    if s >= 0:
        _time_desc += '%s 秒' % s
    return _time_desc


def binary_type(text):
    """转换为byte类型字符串

    @param text: 需要转换的数值
    """
    if isinstance(text, unicode):
        return text.encode('utf-8')
    return str(text)


def intval(text):
    return number_format(text, 0)


def floatval(text):
    return number_format(text, 4)


def concat_ic(text, symbol='€€'):
    args = ('.', '/', '-', '=', '_', ' ', '+', '(', ')', '!', '\\', '$', '%',
            '&', '\'', '*', ',', ':', ';', '<', '|')
    tmp_name = cleartext(text, *args)
    return '%s%s%s' % (text, symbol, tmp_name)


def rfc_headers(headers):
    """获取rfc标准头部信息"""
    if not headers:
        return {}
    _headers = {}
    for k in headers:
        _k = k.replace('_', '-').replace(' ', '-').title()
        _headers[_k] = headers[k]
    return _headers


def unicode_to_str(text, to_str='utf-8'):
    """unicode字符串转字符串"""
    if text and not isinstance(text, unicode):
        return text
    return text.encode(to_str)


def u2b(text):
    """unicode字符串转字符串"""
    return unicode_to_str(text)


def b2u(text):
    """字符串转unicode字符串"""
    return str_to_unicode(text)


def get_default_value(params, key, default=None):
    """安全获取值"""
    if not hasattr(params, '__getitem__'):
        return default
    try:
        _value = params[key]
        if _value is None and default is not None:
            return default
        else:
            return _value
    except KeyError:
        return default


def unixtime(offset=0):
    """获取unix时间戳"""
    return int(time.time()) - offset * 3600


def fetch_email(ename=''):
    '''
    邮箱地址映射
    :param ename:
    :return:
    '''
    if not ename:
        return None
    website = ename.split('@')[-1].split('.')[0]
    site_dict = {
        '163': 'https://mail.163.com/',
        'qq': 'https://mail.qq.com/',
        'foxmail': 'https://mail.qq.com/',
        'gmail': 'https://mail.google.com/',
    }
    if not website in site_dict:
        return None
    return site_dict[website]


def specified_date(start_date=None, end_date=None):
    '''
    创建一个时间段的日期并返回，列表格式
    ['2016-01-01', '2016-01-02', '2016-01-03', '2016-01-04', '2016-01-05']
    :param start_date:
    :param end_date:
    :return:
    '''
    if not start_date:
        start_date = datetime.date(2019, 24, 4).strftime('%d/%m/%Y')
    if not end_date:
        # end_date = datetime.date(2019, 5, 3).strftime('%d/%m/%Y')
        end_date = datetime.date.today().strftime('%m/%d/%Y')

    print(start_date, end_date)
    dframe = pd.date_range(start_date, end_date)
    dlist = []
    for _frame in dframe:
        dlist.append(_frame.strftime('%Y-%m-%d'))

    return dlist


# def get_lottery_key(province=None, lottery_name=None):
#     '''
#     根据地区/彩种名称获取彩种关键词和数据库名称
#     :param province:
#     :return:
#     '''
#     if not province:
#         return None
#     data = mysql.select('t_open_info_spider', condition=[('province', '=', '全国')],
#                         fields=('abbreviation', 'lottery_name', 'province', 'lottery_result'))
#     if not data or lottery_name:
#         return None
#     for _data in data:
#         if _data['lottery_name'] == lottery_name:
#             return _data['abbreviation'], _data['lottery_result']
#     return data


def modify_unit(number=None):
    '''
    处理计量单位
    :param number:
    :return:
    '''
    if not number:
        return 0
    number = cleartext(number)
    if '亿' in number:
        return number
    elif '万' in number:
        return number
    elif '千' in number:
        return number
    else:
        number = number_format(cleartext(number, '元', ','), places=0)

    if len(str(number)) >= 9:
        number = round(number / (10 ** 8), 3)
        return str(number) + '亿'
    elif 9 > len(str(number)) >= 4:
        number = round(number / (10 ** 4), 3)
        return str(number) + '万'
    else:
        return str(number) + '元'


def get_prolist(limit=10):
    """
    获取代理列表
    从url获取改为从数据库获取
    """
    try:
        db = yzwl.DbClass()
        mysql = db.yzwl
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
    except Exception as e:
        return None


def get_session(url=None):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
    })
    if url:
        session.get(url)
    return session


def get_static_file(file_name=None):
    '''
    获取静态文件夹下的静态文件
    :param file_name:
    :return: 如果该文件不存在,则返回空
    '''
    if not file_name:
        return None
    file_type = file_name.split('.')[-1]
    last_dir_path = os.path.abspath(os.path.join(os.path.abspath(__file__), "../.."))
    dir_path = os.path.join(os.path.join(last_dir_path, 'static'), file_type)
    if file_name not in os.listdir(dir_path):
        return None

    file_path = os.path.join(dir_path, file_name)
    return file_path


def regx_find_num(text):
    '''
    使用正则提取数字
    :param text:
    :return:
    [1-9]\d*　     正整数
    -[1-9]\d* 　 负整数
    -?[1-9]\d*　整数
    [1-9]\d*|0　 非负整数
    -[1-9]\d*|0　　 非正整数
    [1-9]\d*\.\d*|0\.\d*[1-9]\d*$　　 正浮点数
    -([1-9]\d*\.\d*|0\.\d*[1-9]\d*)$　 负浮点数
    -?([1-9]\d*\.\d*|0\.\d*[1-9]\d*|0?\.0+|0)$　 浮点数

    '''
    comp = re.compile("[0-9]\d*")
    list_str = comp.findall(text)
    list_num = []
    for item in list_str:
        # item = int(item)
        list_num.append(item)
    return list_num


# print('aa', regx_find_num('2017-09-21(周四)'))

# print(time.mktime(time.strptime('2019-04-25 16:28:39', format)))
# print(time.mktime('2019-04-25 16:28:39'.timetuple()))