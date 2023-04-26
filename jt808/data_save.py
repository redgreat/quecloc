# usr/bin/env python
# 数据存储处理
# conding:utf-8

import pymysql
import taos
from queue import Queue
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

td_conn_name='tdengine'
td_host=db_config.get(td_conn_name, 'host')
td_port=int(db_config.get(td_conn_name, 'port'))
td_username=db_config.get(td_conn_name, 'username')
td_password=db_config.get(td_conn_name, 'password')
td_database=db_config.get(td_conn_name, 'database')
td_charset=db_config.get(td_conn_name, 'charset')

class ConnectionPool(object):
    def __init__(self, engine, max_conn=5):
        #self.engine = 'mysql'
        self.max_conn = max_conn
        self.pool = Queue()
        for i in range(max_conn):
            if engine == 'tdengine':
                conn = taos.connect(
                    host=td_host,
                    port=td_port,
                    database=td_database,
                    user=td_username,
                    password=td_password,
                    charset=td_charset
                )
                print("TDengine Connect Success!")
            else:
                conn = pymysql.connect(
                    host=mysql_host,
                    port=mysql_port,
                    database=mysql_database,
                    user=mysql_username,
                    password=mysql_password,
                    charset=mysql_charset,
                    ssl={'ssl': {"ca": mysql_ssl_path}}
                )
                print("MySQL Connect Success!")
            self.pool.put(conn)

    def acquire(self):
        try:
            conn = self.pool.get(timeout=30)
        except:
            raise RuntimeError("Cannot get a connection from pool")
        return conn

    def release(self, conn):
        if conn:
            self.pool.put(conn)

    def close_all(self):
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()

class DataHandler:

    #def mysql_pool_create():
    #    global mysql_pool
    #    try:
    #        mysql_pool = PooledDB(pymysql, 5, host=mysql_host, database=mysql_database, user=mysql_username,
    #                              password=mysql_password, port=mysql_port, charset=mysql_charset,
    #                              ssl={'ssl': {"ca": mysql_ssl_path}})
    #        logger.info("MySQL Pool Create Success!")
    #    except Exception as e:
    #        logger.error('MySQL Pool Create Failed:{}',e)
    #    return (mysql_pool)
#
    #def td_pool_create():
    #    global td_pool
    #    try:
    #        td_pool = create_engine('taos://{}:{}@{}:{}/{}?charset={}'.format(td_username,
    #                                                                          td_password,
    #                                                                          td_host,
    #                                                                          td_port,
    #                                                                          td_database,
    #                                                                          td_charset) ,
    #                                pool_size=5,
    #                                max_overflow=0)
    #    except Exception as e:
    #        logger.error('TDengine Pool Create Failed:{}',e)
    #    return (td_pool)

    def mysql_save(mysql_pool, sql):
        try:
            with mysql_pool.acquire() as mysql_conn:
                mysql_cur = mysql_conn.cursor()
                try:
                    mysql_cur.execute(sql)
                    mysql_conn.commit()
                except Exception as e:
                    logger.exception('MySQL Error in SQL execution: \'{}\',InsertSQL: {}', e, sql)
        except Exception as e:
            logger.exception('MySQL Connection lost, reconnect Failed: {}', e)

    def td_save(td_pool, sql):
        try:
            td_conn = td_pool.acquire()
            td_cur = td_conn.cursor()
            try:
                td_cur.execute(sql)
                td_conn.commit()
            except Exception as e:
                logger.exception('TDengine Error in SQL execution: \'{}\',InsertSQL: {}', e, sql)
            td_pool.release(td_conn)
        except Exception as e:
            logger.exception('TDengine Connection lost, reconnect Failed: {}', e)