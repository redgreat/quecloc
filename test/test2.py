#!/usr/bin/python
# -*- coding: utf-8 -*

import paho.mqtt.client as mqtt
import json
from geopy import distance
from dbutils.pooled_db import PooledDB
import pymysql
import cx_Oracle
import taosrest
#from supabase import create_client, Client
import configparser
import sys
import os
import time
from loguru import logger
from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)
try:
    if sys.platform.startswith("darwin"):
        lib_dir = os.path.join(os.environ.get("HOME"), "Downloads",
                               "instantclient_21_6")
        cx_Oracle.init_oracle_client(lib_dir=lib_dir)
    elif sys.platform.startswith("win32"):
        lib_dir = r"C:\instantclient_21_6"
        cx_Oracle.init_oracle_client(lib_dir=lib_dir)
except Exception as err:
    print("Whoops!")
    print(err);
    sys.exit(1);

logger.add("locwong.log", colorize=True, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> <level>{message}</level>",
           #backtrace=True, diagnose=True,
           retention="10 days", level="DEBUG")

def get_locatime():
    LocTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return LocTime
db_config=configparser.ConfigParser()
db_config.read_file(open('../dbUtils/connection.cnf', encoding='utf-8', mode='rt'))
IMEI='861551057160301'
b_gps_lng=0
b_gps_lat=0
mysq_pool=''
ora_pool=''

#读取Mqtt配置
mq_conn_name='soyoemqtt'
mq_host=db_config.get(mq_conn_name, 'host')
mq_port=int(db_config.get(mq_conn_name, 'port'))
mq_username=db_config.get(mq_conn_name, 'username')
mq_password=db_config.get(mq_conn_name, 'password')
mq_topic=db_config.get(mq_conn_name, 'topic')
mq_keepalive=int(db_config.get(mq_conn_name, 'keepalive'))

#读取mysql配置
mysql_conn_name='ticloud'
mysql_host=db_config.get(mysql_conn_name, 'host')
mysql_port=int(db_config.get(mysql_conn_name, 'port'))
mysql_username=db_config.get(mysql_conn_name, 'username')
mysql_password=db_config.get(mysql_conn_name, 'password')
mysql_database=db_config.get(mysql_conn_name, 'database')
mysql_ssl_path=db_config.get(mysql_conn_name, 'ssl_path')
mysql_charset=db_config.get(mysql_conn_name, 'charset')

#读取Oracle配置
ora_conn_name='ocloud'
ora_tns_name=db_config.get(ora_conn_name, 'tns_name')
ora_username=db_config.get(ora_conn_name, 'username')
ora_password=db_config.get(ora_conn_name, 'password')
ora_charset=db_config.get(ora_conn_name, 'charset')

#读取TDengine配置
#taos_conn_name='taos'
#taos_host=db_config.get(taos_conn_name, 'host')
#taos_port=db_config.get(taos_conn_name, 'port')
#taos_username=db_config.get(taos_conn_name, 'username')
#taos_password=db_config.get(taos_conn_name, 'password')
#taos_database=db_config.get(taos_conn_name, 'database')
#taos_config=db_config.get(taos_conn_name, 'config')
#taos_timezone=db_config.get(taos_conn_name, 'timezone')

#taos_conn=taos.connect(host=taos_host, user=taos_username, password=taos_password, database=taos_database, port=taos_port, config=taos_config, timezone=taos_timezone)

#TDCloud
taoscloud_conn_name='taoscloud'
taos_url=db_config.get(taoscloud_conn_name, 'url')
taos_token=db_config.get(taoscloud_conn_name, 'token')
#try:
#    taoscloud_pool=PooledDB(taosrest,5,url=taos_url, token=taos_token)
#except Exception as e:
#    print('{}[ERROR]:TDengine Pool Create Fail: {}'.format(get_locatime(), str(e)))

#读取Pg配置
#pg_conn_name='postgres'
#pg_host=db_config.get(pg_conn_name, 'host')
#pg_port=db_config.get(pg_conn_name, 'port')
#pg_username=db_config.get(pg_conn_name, 'username')
#pg_password=db_config.get(pg_conn_name, 'password')
#pg_database=db_config.get(pg_conn_name, 'database')
#
#pg_conn='CREATE STABLE `locwong`.`meters` (`LocTime` TIMESTAMP, `Lat` FLOAT, `Lat` FLOAT) TAGS (`DeviceId` INT);'

def mysql_pool_create():
    global mysql_pool
    try:
        mysql_pool=PooledDB(pymysql,5,host=mysql_host, database=mysql_database, user=mysql_username,
                                    password=mysql_password, port=mysql_port,charset=mysql_charset,
                                    ssl={'ssl': {"ca": mysql_ssl_path}})
        logger.info("MySQL Pool Create Success!")
    except Exception as e:
        #print('{}[ERROR]:MySQL Pool Create Fail: {}'.format(get_locatime(), str(e)))
        logger.error('MySQL Pool Create Failed:{}',e)
    return (mysql_pool)

def ora_pool_create():
    global ora_pool
    try:
        ora_pool=cx_Oracle.SessionPool(user=ora_username, password=ora_password,
                                   dsn=ora_tns_name, min=2, max=5, increment=1, encoding=ora_charset)
        logger.info("Oracle Pool Create Success!")
    except Exception as e:
        #print('{}[ERROR]:Oracle Pool Create Fail: {}'.format(get_locatime(), str(e)))
        logger.error('Oracle Pool Create Failed:{}',e)
    return (ora_pool)

# 连接后事件
def on_connect(client, userdata, flags, respons_code):
    if respons_code == 0:
        #print('{}[INFO]:Connection Succeed!'.format(get_locatime()))
        logger.info('Mqtt Connect Success!')
    else:
        #print('{}[ERROR]:Connect Error status {}'.format(get_locatime(), respons_code))
        logger.error('Mqtt Connect Error,status：{}',respons_code)
    client.subscribe(mq_topic)

# 接收到数据后事件

def on_message(client, userdata, msg):
    global b_gps_lng
    global b_gps_lat
    gpsdata=str(msg.payload).replace('b\'', '').replace('\'', '')
    #logger.info('Mtqq Message Split Success!')
    try:
        gps_lng, gps_lat=gpsdata.split('_', 1)
        gps_lng=float(gps_lng)
        gps_lat=float(gps_lat)
        if isinstance(gps_lng, float) and isinstance(gps_lat, float):
            try:
                gps_distance=distance.distance((b_gps_lat,b_gps_lng), (gps_lat,gps_lng)).m
                logger.info('GPS Point distance with before:{}m', gps_distance)
                if gps_distance > 5:
                    mysql_save(mysql_pool, gps_lng, gps_lat)
                    ora_save(ora_pool, gps_lng, gps_lat)
                    taos_save(gps_lng, gps_lat)
                else:
                    logger.info('GPS Point distance with before less than 5m,Not insert!')
                b_gps_lat=gps_lat
                b_gps_lng=gps_lng
            except Exception as e:
                logger.exception('GPS data error: {},Payload:{}', e, gpsdata)
                pass
    except Exception as e:
        logger.exception('GPS data error or No gos singal: {},Payload:{}', e, gpsdata)
        pass

def main():
    mysql_pool_create()
    ora_pool_create()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(username=mq_username, password=mq_password)
    client.connect(host=mq_host, port=mq_port, keepalive=mq_keepalive)
    client.loop_forever()

#MySQL数据保存
def mysql_save(mysql_pool, gps_lng, gps_lat):

    sql="INSERT INTO `locdaily` (DeviceIMEI,Lat,Lng,LocTime) VALUES ({},{},{},\'{}\');".format(IMEI, gps_lat, gps_lng, get_locatime())

    try:
        with mysql_pool.connection() as mysql_conn:
            mysql_cur=mysql_conn.cursor()
            try:
                mysql_cur.execute(sql)
                mysql_conn.commit()
                logger.info('MySQL Data Insert Success!')
            except Exception as e:
                logger.exception('MySQL Error in SQL execution: {},InsertSQL: {}', e, sql)
    except Exception as e:
        #print('{}[ERROR]:MySQL Connection lost, reconnect FAILED： {}'.format(get_locatime(),str(e)))
        logger.exception('MySQL Connection lost, reconnect Failed: {}', e)

#Oracle数据保存
def ora_save(ora_pool, gps_lng, gps_lat):

    sql="INSERT INTO \"WANGCW\".\"LOCDAILY\"(\"DeviceIMEI\",\"Lat\",\"Lng\",\"LocTime\") VALUES(\'{}\',{},{},TO_TIMESTAMP(\'{}\',\'YYYY-MM-DD HH24:MI:SS\'))".format(IMEI, gps_lat, gps_lng, get_locatime())
    try:
        #ora_conn = cx_Oracle.connect(user=ora_username, password=ora_password, dsn=ora_tns_name, encoding=ora_charset)
        with ora_pool.acquire() as ora_conn:
            ora_cur=ora_conn.cursor()
            try:
                ora_cur.execute(sql)
                ora_conn.commit()
                #print('{}[INFO]:Oracle Data Insert Success!'.format(get_locatime()))
                logger.info('Oracle Data Insert Success!')
            except Exception as e:
                #print('{}[ERROR]:Oracle Error in SQL execution: {}'.format(get_locatime(), str(e)))
                logger.exception('Oracle Error in SQL execution: {},InsertSQL: {}', e, sql)
            #ora_pool.release(ora_conn)
    except Exception as e:
        #print('{}[ERROR]:Oracle Connection lost, reconnect FAILED: {}'.format(get_locatime(), str(e)))
        logger.exception('Oracle Connection lost, reconnect Failed: {}', e)

#TDengine数据保存
def taos_save(gps_lng, gps_lat):

    sql="INSERT INTO `test`.`{0}` USING `test`.`locdaily`(`DeviceIMEI`) TAGS(\'{0}\')(`LocTime`, `Lat`, `Lng`) VALUES(\'{1}\', {2}, {3});".format(IMEI, get_locatime(), gps_lat, gps_lng)
    try:
        taoscloud_conn = taosrest.connect(url=taos_url, token=taos_token)
        taos_cur = taoscloud_conn.cursor()
        try:
            taos_cur.execute(sql)
            taoscloud_conn.commit()
            #print('{}[INFO]:TDengine Data Insert Success!'.format(get_locatime()))
            logger.info('TDengine Data Insert Success!')
            taos_cur.close()
        except Exception as e:
            logger.exception('TDengine Error in SQL execution: {},InsertSQL: {}', e, sql)
            #print('{}[ERROR]:TDengine Error in SQL execution: {}'.format(get_locatime(), str(e)))
        taoscloud_conn.close()
    except Exception as e:
        #print('{}[ERROR]:TDengine Connection lost, reconnect FAILED: {}'.format(get_locatime(), str(e)))
        logger.exception('TDengine Connection lost, reconnect Failed: {}', e)

#Pg数据保存

if __name__ == '__main__':
    main()