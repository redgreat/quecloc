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

td_conn_name='tdengine'
td_host=db_config.get(td_conn_name, 'host')
td_port=int(db_config.get(td_conn_name, 'port'))
td_username=db_config.get(td_conn_name, 'username')
td_password=db_config.get(td_conn_name, 'password')
td_database=db_config.get(td_conn_name, 'database')
td_charset=db_config.get(td_conn_name, 'charset')

class ConnectionPool(object):
    def __init__(self, engine, max_conn=5):
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
        return self.pool.get()

    def release(self, conn):
        self.pool.put(conn)

    def close_all(self):
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()

class DataHandler:
    def td_save(td_pool, sql):
        try:
            td_conn = td_pool.acquire()
            td_cur = td_conn.cursor()
            try:
                td_cur.execute(sql)
                r = td_cur.fetchall()
                print(r)
                #td_conn.commit()
            except Exception as e:
                logger.exception('TDengine Error in SQL execution: \'{}\',InsertSQL: {}', e, sql)
        except Exception as e:
            logger.exception('TDengine Connection lost, reconnect Failed: {}', e)

td_pool = ConnectionPool('tdengine', max_conn=3)
sql="SELECT SERVER_VERSION();"
DataHandler.td_save(td_pool, sql)

#pool.release(conn)