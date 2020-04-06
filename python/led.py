# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 13:47:51 2020

@author: -
"""

import requests

import json


url = '192.168.7.2'
id = 1
pwd = '83e47941d9e930f6'  # pwd lighthub

# LOGIN
try:
    host = 'http://' + url + ':8181/api/login'
    a = requests.post(host, json={'username': 'admin', 'password': pwd}, verify=False)
    cookiejar = a.cookies
except requests.RequestException as err:
    print('login error: ', err)


# LOAD VIDEO
try:
    video = 'led_test_all.dsf'
    args = [('file', (video, open(video, 'rb'), 'application/json'))]
    requests.post('http://' + url + ':8181/api/gateway/video', files=args, cookies=cookiejar, verify=False)
except Exception as err:
    print('error: ',err)


# PLAY VIDEO
try:
    host = 'http://' + url + ':8181/api/luminaire/' + str(id) + '/command/PLAY_VIDEO_FILE'
    data = {'arg': './data/video1.json'}
    requests.post(host, json=data, cookies=cookiejar, verify=False)
except requests.RequestException as err:
    print(err)