#! /usr/bin/python
# -*- coding: utf-8 -*-
import requests

__author__ = 'snow'
__time__ = '2019/4/15'

url = 'http://www.espn.com/nba/team/roster/_/name/bos'

res = requests.get(url=url)

print('res', res.text)
