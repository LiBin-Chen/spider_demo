#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''
import json
import time
import pandas as pd
from packages import yzwl

db = yzwl.DbClass()

mysql = db.local_yzwl


def main():
    expect = '0'
    # big_list = {}
    while 1:
        data = mysql.select('game_ahks_result', condition={'expect': ('>', expect)},
                            fields=('id', 'open_code', 'expect'),
                            order='expect ASC',
                            limit=2)
        expect = data[0].get('expect')
        if not data:
            print('wrong')
        print('data',data)
        continue
        exit()
        # for data in info:
        expect = data.get('expect')
        open_code = data.get('open_code')

        open_code_list = open_code.split(',')
        print('open_code', open_code)
        key_dict = [
            'min', 'mid', 'max']
        big_list = {}

        for i in range(len(open_code_list)):
            _code = open_code_list[i]
            omit_list = {}
            omit_list = []
            for j in range(10):
                if int(_code) != j:
                    omit_list.append(1)
                    # omit_list.append(j)
                else:
                    omit_list.append(0)
                    # omit_list[j] = 0

            print('omit', omit_list)
            # big_list.append(omit_list)
            big_list[key_dict[i]] = omit_list
        print('big_list', big_list)

        big_list = json.dumps(big_list, ensure_ascii=False)
        mysql.update('game_ahks_result', condition={'id': data['id']}, data={'trend_chart': big_list})

        # pd_data=pd.DataFrame(big_list)
        # print('pd_data',pd_data)

        # exit()
        # with open('test.txt', 'r') as fp:
        #     content = fp.read()
        #     print('content', content)
        #     if content:
        #         content = json.loads(content)
        #         print('content',type(content))
        #         min_data = content['min']
        #         mid_data = content['mid']
        #         max_data = content['max']
        #
        #         min_new = big_list['min']
        #         mid_new = big_list['mid']
        #         max_new = big_list['max']
        #         # for i in range(len(min_data)):
        #         #     pass

        # with open('test.txt', 'a+') as fp:
        #     fp.write(json.dumps(big_list, ensure_ascii=False))
        #
        # time.sleep(100)
        exit()
        # print('data', data)


if __name__ == '__main__':
    main()
