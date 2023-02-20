#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests
from flask import Flask,request
from gevent import pywsgi
from datetime import datetime

simplefilter(action='ignore', category=FutureWarning)
logger.add("/home/wangcan/locwong/iotwong.log", colorize=True, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> <level>{message}</level>",
           backtrace=True, diagnose=True, retention="10 days", level="DEBUG")
db_config=configparser.ConfigParser()
db_config.read_file(open('/home/wangcan/locwong/con.cnf', encoding='utf-8', mode='rt'))
IMEI='868977061978771'
b_gps_lng=0
b_gps_lat=0
mysql_pool=''
ora_pool=''

# 企业微信机器人Id
wx_key="ea50a2d0-2d51-4ba3-a90c-66919a51ca01"
wx_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={}'.format(wx_key)
wx_headers = {'Content-Type':'application/json'}
wx_mentioned_list = ['@all']

mysql_conn_name='ticloud'
mysql_host=db_config.get(mysql_conn_name, 'host')
mysql_port=int(db_config.get(mysql_conn_name, 'port'))
mysql_username=db_config.get(mysql_conn_name, 'username')
mysql_password=db_config.get(mysql_conn_name, 'password')
mysql_database=db_config.get(mysql_conn_name, 'database')
mysql_ssl_path=db_config.get(mysql_conn_name, 'ssl_path')
mysql_charset=db_config.get(mysql_conn_name, 'charset')

def send_msg (content):
    data = {"msgtype": "text","text": {"content": content.decode(),"mentioned_list": wx_mentioned_list}}
    requests.post(url = wx_url, json = data, headers = wx_headers)
    return '{"success":"true"}'

def mysql_pool_create():
    global mysql_pool
    try:
        mysql_pool = PooledDB(pymysql, 5, host=mysql_host, database=mysql_database, user=mysql_username,
                              password=mysql_password, port=mysql_port, charset=mysql_charset,
                              ssl={'ssl': {"ca": mysql_ssl_path}})
        logger.info("MySQL Pool Create Success!")
    except Exception as e:
        logger.error('MySQL Pool Create Failed:{}',e)
    return (mysql_pool)

def mysql_save(mysql_pool, sql):
    try:
        with mysql_pool.connection() as mysql_conn:
            mysql_cur = mysql_conn.cursor()
            try:
                mysql_cur.execute(sql)
                mysql_conn.commit()
                logger.info('MySQL Data Insert Success!')
            except Exception as e:
                logger.exception('MySQL Error in SQL execution: {},InsertSQL: {}', e, sql)
    except Exception as e:
        logger.exception('MySQL Connection lost, reconnect Failed: {}', e)

app = Flask(__name__)

@app.route("/locwong/wa200",methods=['POST'])
def event():
    req_data = request.form
    req_type = req_data.get("type")
    BTUtcTime = req_data.get("BTUtcTime")
    steps = req_data.get("steps")
    heartbeat = req_data.get("heartbeat")
    bodyTemperature = req_data.get("bodyTemperature")
    bloodSugar = req_data.get("bloodSugar")
    Diastolic = req_data.get("Diastolic")
    Shrink = req_data.get("Shrink")
    BloodOxygen = req_data.get("BloodOxygen")
    SleepType = req_data.get("sleepType")
    SleepStartTime = req_data.get("startTime")
    SleepEndTime = req_data.get("endTime")
    SleepMinute = req_data.get("minute")
    Signal = req_data.get("Signal")
    Battery = req_data.get("battery")
    GPSLat = req_data.get("latStr")
    GPSLng = req_data.get("lngStr")
    SpeedStr = req_data.get("speedStr")
    Lat = req_data.get("Latitude")
    Lng = req_data.get("Longitude")

    AlertInfo = req_data.get("AlertInfo")
    HeartNum = req_data.get("heartNum")
    LastTemper = req_data.get("lastTemper")



    if req_type == 16:
        then
        sql="""
        
        """
        mysql_save(mysql_pool, sql)

    elseif req_type in (4,5,6,8,10,11,12,14,31,58):
        then
        sql="""
        """
        mysql_save(mysql_pool, sql)

    elseif req_type in (18,19,20,21,22,23):
        then
        send_msg (req_data)

    return '{"success":"true"}'

server = pywsgi.WSGIServer(('10.0.0.187', 8089), app)
server.serve_forever()