#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests
import pymysql
from flask import Flask,request
from gevent import pywsgi
from dbutils.pooled_db import PooledDB
from datetime import datetime
import math
from loguru import logger
import configparser
from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)
logger.add("iotwong.log", colorize=True, #format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> <level>{message}</level>",
           backtrace=True, diagnose=True, retention="10 days", level="DEBUG")
db_config=configparser.ConfigParser()
db_config.read_file(open('../dbUtils/connection.cnf', encoding='utf-8', mode='rt'))
x_pi = math.pi * 3000.0 / 180.0
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 偏心率平方
IMEI='868977061978771'
gps_lng=0
gps_lat=0
mysql_pool=''
ora_pool=''

mysql_dic = {"BTUtcTime": "UtcTime",
             "steps": "Steps",
             "heartbeat": "Heartbeat",
             "roll": "Roll",
             "bodyTemperature": "BodyTemperature",
             "wristTemperature": "WristTemperature",
             "bloodSugar": "BloodSugar",
             "Diastolic": "Diastolic",
             "Shrink": "Shrink",
             "BloodOxygen": "BloodOxygen",
             "sleepType": "SleepType",
             "startTime": "SleepStartTime",
             "endTime": "SleepEndTime",
             "minute": "SleepMinute",
             "Signal": "Signal",
             "battery": "Battery",
             "latStr": "Lat",
             "lngStr": "Lng",
             "speedStr": "SpeedStr",
             "Latitude": "Lat",
             "Longitude": "Lng"}

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

def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 *
            math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * math.pi) + 40.0 *
            math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * math.pi) + 320 *
            math.sin(lat * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 *
            math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * math.pi) + 40.0 *
            math.sin(lng / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * math.pi) + 300.0 *
            math.sin(lng / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

def out_of_china(lng, lat):
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)

def wgs84_to_gcj02(lng, lat):
    if out_of_china(lng, lat):  # 判断是否在国内
        return [lng, lat]
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [mglng, mglat]

def send_msg (content):
    try:
        data = {"msgtype": "text","text": {"content": content.decode(),"mentioned_list": wx_mentioned_list}}
        requests.post(url = wx_url, json = data, headers = wx_headers)
        logger.info('Message Send Success!')
    except Exception as e:
        logger.error('Message Send Failed:{}',e)
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
                logger.exception('MySQL Error in SQL execution: \'{}\',InsertSQL: {}', e, sql)
    except Exception as e:
        logger.exception('MySQL Connection lost, reconnect Failed: {}', e)

app = Flask(__name__)

@app.route("/locwong/wa200",methods=['POST'])
def event():
    req_data = request.form
    logger.info('ReceiveData:{}', req_data)
    req_type = req_data.get("type")
    sql_cols = ''
    sql_vals = ''

    if req_type in ('4', '5', '6', '8', '10', '11', '12', '14', '31', '58'):
        try:
            for sql_col, sql_val in req_data.items():
                print(sql_col, sql_val)
                if sql_col in ('BTUtcTime', 'steps', 'heartbeat', 'roll', 'bodyTemperature', 'wristTemperature',
                               'bloodSugar', 'Diastolic', 'Shrink', 'BloodOxygen', 'sleepType', 'startTime',
                               'endTime', 'minute', 'Signal', 'battery', 'latStr', 'lngStr','Latitude', 'Longitude', 'Speed'):
                    sql_col=mysql_dic.get(sql_col, sql_col)
                    if req_type == '16' and sql_col in ('Lat','Lng'):
                        req_latStr = req_data.get("latStr")
                        req_lngStr = req_data.get("lngStr")
                        try:
                            gps_lat = float(req_latStr)
                            gps_lng = float(req_lngStr)
                            gps_dic = {"req_latStr": gps_lat, "req_lngStr": gps_lng}
                            sql_val = gps_dic.get(sql_val, sql_val)
                        except Exception as e:
                            logger.exception('GPS Data Convert Error:{},[Lat({}),Lng({})]', e, req_latStr, req_lngStr)
                    sql_cols += '`' + sql_col + '`,'
                    sql_vals += '\'' + str(sql_val) + '\','
            sql_cols = sql_cols.strip(',')
            print(sql_cols, sql_vals)
            if sql_cols != '':
                sql_vals = sql_vals.strip(',')
                sql = "REPLACE INTO `watchdaily`({}) VALUES({});".format(sql_cols, sql_vals)
                print(sql)
                mysql_save(mysql_pool, sql)
                logger.info('Column and Values Data parase success!')
        except Exception as e:
            logger.exception('Column and Values Data Error:{}', e)
    elif req_type in ('18','19','20','21','22','23'):
       AlertInfo = req_data.get("AlertInfo")
       HeartNum = req_data.get("heartNum")
       LastTemper = req_data.get("lastTemper")
       sql="""
       INSERT INTO `watchalarm`(AlertType,AlertInfo,HeartNum,LastTemper)
       VALUES(\'{}\',\'{}\',\'{}\',\'{}\');
       """.format(req_type,AlertInfo,HeartNum,LastTemper)
       send_msg (AlertInfo)
       mysql_save(mysql_pool, sql)
    else:
        logger.info('ReceiveData:{}', req_data)
    return '{"success":"true"}'

if __name__ == '__main__':
    mysql_pool_create()
    server = pywsgi.WSGIServer(('10.12.4.35', 8089), app)
    server.serve_forever()