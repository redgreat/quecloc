#!/usr/bin/python
# -*- coding: utf-8 -*

import paho.mqtt.client as mqtt
from geopy import distance
import pynmea2
from dbutils.pooled_db import PooledDB
import pymysql
import taosrest
import configparser
import time
from loguru import logger
from warnings import simplefilter

simplefilter(action='ignore', category=FutureWarning)
logger.add("air780eg.log", colorize=True, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> <level>{message}</level>",
           backtrace=True, diagnose=True, retention="10 days", level="DEBUG")
db_config=configparser.ConfigParser()
db_config.read_file(open('../dbUtils/connection.cnf', encoding='utf-8', mode='rt'))
IMEI='864269067611349'
b_gps_lng=0
b_gps_lat=0
mysql_pool=''
ora_pool=''

mq_conn_name='air780eg'
mq_host=db_config.get(mq_conn_name, 'host')
mq_port=int(db_config.get(mq_conn_name, 'port'))
mq_username=db_config.get(mq_conn_name, 'username')
mq_password=db_config.get(mq_conn_name, 'password')
mq_topic=db_config.get(mq_conn_name, 'topic')
mq_keepalive=int(db_config.get(mq_conn_name, 'keepalive'))

mysql_conn_name='ticloud'
mysql_host=db_config.get(mysql_conn_name, 'host')
mysql_port=int(db_config.get(mysql_conn_name, 'port'))
mysql_username=db_config.get(mysql_conn_name, 'username')
mysql_password=db_config.get(mysql_conn_name, 'password')
mysql_database=db_config.get(mysql_conn_name, 'database')
mysql_ssl_path=db_config.get(mysql_conn_name, 'ssl_path')
mysql_charset=db_config.get(mysql_conn_name, 'charset')

taoscloud_conn_name='taoscloudcn'
taos_url=db_config.get(taoscloud_conn_name, 'url')
taos_token=db_config.get(taoscloud_conn_name, 'token')

def get_locatime():
    LocTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return LocTime

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

def on_connect(client, userdata, flags, respons_code):
    if respons_code == 0:
        logger.info('Mqtt Connect Success!')
    else:
        logger.error('Mqtt Connect Error,status：{}', respons_code)
    client.subscribe(mq_topic)

def on_message(client, userdata, msg):
    global b_gps_lng
    global b_gps_lat
    msgrec = msg.payload.decode()
    gpsdata = pynmea2.parse(msgrec)
    if msgrec.startswith('$GPRMC') or msgrec.startswith('$GNRMC'):
        try:
            gps_lat = gpsdata.latitude
            gps_lng = gpsdata.longitude
            if isinstance(gps_lng, float) and isinstance(gps_lat, float):
                try:
                    gps_distance = distance.distance((b_gps_lat, b_gps_lng), (gps_lat, gps_lng)).m
                    logger.info('GPS Point distance with before:{}m', gps_distance)
                    if gps_distance >= 1:
                        #mysql_save(mysql_pool, gps_lng, gps_lat)
                        #ora_save(ora_pool, gps_lng, gps_lat)
                        taos_save(gps_lng, gps_lat)
                    else:
                        logger.info('GPS Point distance with before less than 8m,Not insert!')
                    b_gps_lat = gps_lat
                    b_gps_lng = gps_lng
                except Exception as e:
                    logger.exception('GPS data error: {},Payload:{}', e, gpsdata)
        except Exception as e:
            logger.exception('GPS data error or No gos singal: {},Payload:{}', e, gpsdata)

def main():
    #mysql_pool_create()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(username=mq_username, password=mq_password)
    client.connect(host=mq_host, port=mq_port, keepalive=mq_keepalive)
    client.loop_forever()

def mysql_save(mysql_pool, gps_lng, gps_lat):
    sql="INSERT INTO `locdaily` (DeviceIMEI,Lat,Lng,LocTime) VALUES ({},{},{},\'{}\');".format(IMEI, gps_lat, gps_lng, get_locatime())
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

def taos_save(gps_lng, gps_lat):
    sql = "INSERT INTO `dailywong`.`{0}` USING `dailywong`.`locdaily`(`DeviceIMEI`) TAGS(\'{0}\')(`LocTime`, `Lat`, `Lng`) VALUES(\'{1}\', {2}, {3});".format(
        IMEI, get_locatime(), gps_lat, gps_lng)
    #print(sql)
    try:
        taoscloud_conn = taosrest.connect(url=taos_url, token=taos_token)
        taos_cur = taoscloud_conn.cursor()
        try:
            taos_cur.execute(sql)
            taoscloud_conn.commit()
            logger.info('TDengine Data Insert Success!')
            taos_cur.close()
        except Exception as e:
            logger.exception('TDengine Error in SQL execution: {},InsertSQL: {}', e, sql)
        taoscloud_conn.close()
    except Exception as e:
        logger.exception('TDengine Connection lost, reconnect Failed: {}', e)

if __name__ == '__main__':
    main()