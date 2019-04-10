# -*- coding: utf-8 -*-
import os
import socket
import select
import sys

import pymongo
import threading

try:
    import config as setting
    from database import db_mysql
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import config as setting
    from database import db_mysql

try:
    import json
except ImportError:
    import simplejson as json


def _catch_mongo_error(func):
    """捕获mongo错误"""

    def wrap(self):
        try:
            return func(self)
        except (select.error, socket.error, pymongo.errors.AutoReconnect, pymongo.errors.CursorNotFound) as e:
            self.__mongo = None
            return func(self)

    return wrap


class MySQL(object):
    '''mysql操作'''

    def __init__(self, config=None):
        self.config = config if config else setting.DATABASES
        self.__db_pool = {}

    def __getattr__(self, db):
        if db not in setting.DB_KEY.values():
            raise AttributeError('%s 属性不存在' % (db,))
        if db in self.__db_pool:
            return self.__db_pool[db]
        _db_config = self.config['mysql'][1].copy()
        _db_config['tablepre'] = ''
        _db_config['db_fields_cache'] = 0
        _db_config['data_type'] = 'dict'
        mysql = db_mysql(**_db_config)
        mysql.select_db(db)
        self.__db_pool[db] = mysql
        return mysql

    def get_database(self, name):
        """获取数据库对象"""
        return getattr(self, name)

    def __del__(self):
        try:
            for k in self.__db_pool:
                del self.__db_pool[k]
        except:
            pass


class DbClass(object):

    def __init__(self, config=None, collection=None):
        self.__yzwl = None
        self.__local_yzwl = None
        self.__test_yzwl = None
        self.__mongo = None
        self.__supplier = None
        self.config = config if config else setting.DATABASES
        self.__del = []  # 原来用set,报错
        self.collection = collection

    @property
    def yzwl(self):
        if not self.__yzwl:
            _db_config = self.config['mysql'][1].copy()
            _db_config['tablepre'] = ''
            # _db_config['tablepre'] = 'zl_'
            _db_config['db_fields_cache'] = 0
            _db_config['data_type'] = 'dict'
            self.__yzwl = db_mysql(**_db_config)
            if self.__yzwl not in self.__del:
                self.__del.append(self.__yzwl)
        return self.__yzwl

    @property
    def test_yzwl(self):
        if not self.__test_yzwl:
            _db_config = self.config['mysql'][1].copy()
            _db_config['tablepre'] = ''
            # _db_config['tablepre'] = 'zl_'
            _db_config['db_fields_cache'] = 0
            _db_config['data_type'] = 'dict'
            self.__test_yzwl = db_mysql(**_db_config)
            if self.__test_yzwl not in self.__del:
                self.__del.append(self.__test_yzwl)
        return self.__test_yzwl

    @property
    def local_yzwl(self):
        if not self.__local_yzwl:
            _db_config = self.config['mysql'][2].copy()
            _db_config['tablepre'] = ''
            # _db_config['tablepre'] = 'zl_'
            _db_config['db_fields_cache'] = 0
            _db_config['data_type'] = 'dict'
            self.__local_yzwl = db_mysql(**_db_config)
            if self.__local_yzwl not in self.__del:
                self.__del.append(self.__local_yzwl)
        return self.__local_yzwl

    @property
    def supplier(self):
        if not self.__supplier:
            self.__supplier = MySQL(self.config)
            if self.supplier not in self.__del:
                self.__del.append(self.supplier)
            # self.__del.add(self.supplier)
        return self.__supplier

    @property
    @_catch_mongo_error
    def mongo(self):
        default_collection = 'data'
        if not self.__mongo:
            _collection = self.collection if self.collection else default_collection
            _config = self.config['mongo'][0] + _collection
            conn = pymongo.MongoClient(_config)
            self.__mongo = conn.get_database()
            # print('conn', conn)
            # self.__del.add(conn)
            if conn not in self.__del:
                self.__del.append(conn)
            # print('self.mongo', self.mongo)
            # self.__del.add(self.mongo)
            if self.mongo not in self.__del:
                self.__del.append(self.mongo)
        return self.__mongo

    def __del__(self):
        for k in self.__del:
            try:
                del k
            except:
                pass


class DbSession(object):
    """针对多线程调用Db封装，多线程调用安全处理"""

    def __init__(self, config=None, collection=None):
        self.thread_queue = {}
        self.config = config
        self.collection = collection

    def __getattr__(self, attr):
        tname = threading.current_thread().name
        if tname not in self.thread_queue:
            self.thread_queue[tname] = DbClass(self.config, self.collection)
        return getattr(self.thread_queue[tname], attr)


db = DbSession()

# 测试
if __name__ == '__main__':
    # mongo的测试
    # db = DbSession()
    # col = db.mongo['BTCUSDT.BINANCE']
    # print(col)
    # col.save({'a': 1})
    # data = col.find_one()
    # print('data', data)

    # mysql 测试
    mysql = db.yzwl

    data = mysql.select('t_lottery', fields=('abbreviation'))
    item = {}
    for _data in range(len(data)):
        item[_data] = data[_data]['abbreviation']

    print(json.dumps(item, indent=4))

    exit()
    limit = 2
    count = 0
    print('1111')
    while 1:
        data = mysql.select('t_game_basketball_event', condition=[('id', '>', count)],
                            limit=limit)  # 不指定fields 则获取所有的字段
        count += limit
        print(data)
        if not data:
            break
