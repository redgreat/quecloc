#!/usr/bin/python
# -*- coding: utf-8 -*

import paho.mqtt.client as mqtt
import json
import pymysql
import cx_Oracle
import taosrest
from supabase import create_client, Client
import configparser
import sys
import os
import time
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

def get_locatime():
    LocTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return LocTime
db_config=configparser.ConfigParser()
db_config.read_file(open('../dbUtils/connection.cnf', encoding='utf-8', mode='rt'))
IMEI='861551057160301'

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

#读取Pg配置
#pg_conn_name='postgres'
#pg_host=db_config.get(pg_conn_name, 'host')
#pg_port=db_config.get(pg_conn_name, 'port')
#pg_username=db_config.get(pg_conn_name, 'username')
#pg_password=db_config.get(pg_conn_name, 'password')
#pg_database=db_config.get(pg_conn_name, 'database')
#
#pg_conn='CREATE STABLE `locwong`.`meters` (`LocTime` TIMESTAMP, `Lat` FLOAT, `Lat` FLOAT) TAGS (`DeviceId` INT);'

# 连接后事件
def on_connect(client, userdata, flags, respons_code):
    if respons_code == 0:
        print('{}[INFO]:Connection Succeed!'.format(get_locatime()))
    else:
        print('{}[ERROR]:Connect Error status {}'.format(get_locatime(), respons_code))
    client.subscribe(mq_topic)

# 接收到数据后事件
def on_message(client, userdata, msg):
    # 打印消息数据
    #print("payload", msg.payload)
    jsondata=json.loads(msg.payload)
    mysql_save(jsondata)
    ora_save(jsondata)
    taos_save(jsondata)

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(username=mq_username, password=mq_password)
    client.connect(host=mq_host, port=mq_port, keepalive=mq_keepalive)
    client.loop_forever()

#MySQL数据保存
def mysql_save(jsondata):

    sql = "INSERT INTO `locdaily` (DeviceIMEI,Lat,Lng,LocTime) VALUES ({},{},{},\'{}\');".format(IMEI, float(jsondata['Lat']), float(jsondata['Lng']), get_locatime())

    try:
        mysql_conn=pymysql.connect(host=mysql_host, database=mysql_database, user=mysql_username,
                                   password=mysql_password, port=mysql_port,charset=mysql_charset,
                                   ssl={'ssl': {"ca": mysql_ssl_path}})
        mysql_cur=mysql_conn.cursor()
        try:
            mysql_cur.execute(sql)
            mysql_conn.commit()
            print('{}[INFO]:MySQL Data Insert Success!'.format(get_locatime()))
            mysql_cur.close()
        except Exception as e:
            print('{}[ERROR]:MySQL Error in SQL execution: {}'.format(get_locatime(),str(e)))
        mysql_conn.close()
    except Exception as e:
        print('{}[ERROR]:MySQL Connection lost, reconnect FAILED： {}'.format(get_locatime(),str(e)))

#Oracle数据保存
def ora_save(jsondata):

    sql="INSERT INTO \"WANGCW\".\"LOCDAILY\"(\"DeviceIMEI\",\"Lat\",\"Lng\",\"LocTime\") VALUES(\'{}\',{},{},TO_TIMESTAMP(\'{}\',\'YYYY-MM-DD HH24:MI:SS\'))".format(IMEI, float(jsondata['Lat']), float(jsondata['Lng']), get_locatime())
    try:
        ora_conn = cx_Oracle.connect(user=ora_username, password=ora_password, dsn=ora_tns_name, encoding=ora_charset)
        ora_cur=ora_conn.cursor()
        try:
            ora_cur.execute(sql)
            ora_conn.commit()
            print('{}[INFO]:Oracle Data Insert Success!'.format(get_locatime()))
            ora_cur.close()
        except Exception as e:
            print('{}[ERROR]:Oracle Error in SQL execution: {}'.format(get_locatime(), str(e)))
        ora_conn.close()
    except Exception as e:
        print('{}[ERROR]:Oracle Connection lost, reconnect FAILED: {}'.format(get_locatime(), str(e)))

#TDengine数据保存
def taos_save(jsondata):

    sql="INSERT INTO `test`.`{0}` USING `test`.`locdaily`(`DeviceIMEI`) TAGS(\'{0}\')(`LocTime`, `Lat`, `Lng`) VALUES(\'{1}\', {2}, {3});".format(IMEI, get_locatime(), float(jsondata['Lat']), float(jsondata['Lng']))

    try:
        taoscloud_conn = taosrest.connect(url=taos_url, token=taos_token)
        taos_cur = taoscloud_conn.cursor()
        try:
            taos_cur.execute(sql)
            taoscloud_conn.commit()
            print('{}[INFO]:TDengine Data Insert Success!'.format(get_locatime()))
            taos_cur.close()
        except Exception as e:
            print('{}[ERROR]:TDengine Error in SQL execution: {}'.format(get_locatime(), str(e)))
        taoscloud_conn.close()
    except Exception as e:
        print('{}[ERROR]:TDengine Connection lost, reconnect FAILED: {}'.format(get_locatime(), str(e)))

#Pg数据保存

if __name__ == '__main__':
    main()