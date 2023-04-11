# usr/bin/env python
# 数据存储处理
# conding:utf-8

import pymysql
from dbutils.pooled_db import PooledDB
from loguru import logger
import configparser
from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)
logger.add("iotwong.log", colorize=True, #format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> <level>{message}</level>",
           backtrace=True, diagnose=True, retention="10 days", level="DEBUG")
db_config=configparser.ConfigParser()
db_config.read_file(open('../dbUtils/connection.cnf', encoding='utf-8', mode='rt'))

mysql_conn_name='ticloud'
mysql_host=db_config.get(mysql_conn_name, 'host')
mysql_port=int(db_config.get(mysql_conn_name, 'port'))
mysql_username=db_config.get(mysql_conn_name, 'username')
mysql_password=db_config.get(mysql_conn_name, 'password')
mysql_database=db_config.get(mysql_conn_name, 'database')
mysql_ssl_path=db_config.get(mysql_conn_name, 'ssl_path')
mysql_charset=db_config.get(mysql_conn_name, 'charset')

class DataHandler:

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
                    #sql = sql.replace("'","\\'")
                    #sql = sql.replace("(\\'","('")
                    #sql = sql.replace("\\')","')")
                    mysql_cur.execute(sql)
                    mysql_conn.commit()
                    #logger.info('MySQL Data Insert Success!')
                except Exception as e:
                    logger.exception('MySQL Error in SQL execution: \'{}\',InsertSQL: {}', e, sql)
        except Exception as e:
            logger.exception('MySQL Connection lost, reconnect Failed: {}', e)