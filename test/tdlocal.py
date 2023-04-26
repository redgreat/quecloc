# usr/bin/env python
# conding:utf-8

import taos
from queue import Queue

class ConnectionPool(object):
    def __init__(self, max_conn=5):
        self.max_conn = max_conn
        self.pool = Queue()
        for i in range(max_conn):
            conn = taos.connect(
                host="nas.wongcw.cn",
                user="wangcw",
                password="Mm19890425",
                database="dailywong",
                port=6030,
                config="/etc/taos",  # for windows the default value is C:\TDengine\cfg
                timezone="Asia/Shanghai"
            )
            self.pool.put(conn)

    def acquire(self):
        return self.pool.get()

    def release(self, conn):
        self.pool.put(conn)

    def close_all(self):
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()

#pool = ThreadedConnectionPool(
#    creator=taos.connect,
#    host="nas.wongcw.cn",
#    user="wangcw",
#    password="Mm19890425",
#    database="dailywong",
#    port=6030,
#    config="/etc/taos",  # for windows the default value is C:\TDengine\cfg
#    timezone="Asia/Shanghai",
#    maxconnections=10
#)
#conn: taos.TaosConnection = taos.connect(host="nas.wongcw.cn",
#                                         user="wangcw",
#                                         password="Mm19890425",
#                                         database="dailywong",
#                                         port=6030,
#                                         config="/etc/taos",  # for windows the default value is C:\TDengine\cfg
#                                         timezone="Asia/Shanghai")  # default your host's timezone
#
pool = ConnectionPool(max_conn=3)
#conn = pool.acquire()
#cursor = conn.cursor()
#cursor.execute("SELECT SERVER_VERSION();")
#result = cursor.fetchall()
#print(result)
#pool.release(conn)

with pool.acquire() as td_conn:
    td_cur = td_conn.cursor()
    td_cur.execute("SELECT SERVER_VERSION();")
    result = td_cur.fetchall()
    print(result)
    pool.release(conn)

#pool = ConnectionPool(max_conn=3)
#with pool.acquire() as conn:
#    cursor = conn.cursor()
#    server_version = cursor.execute("""SELECT SERVER_VERSION();""")
#    pool.release(conn)

#server_version = conn.server_info
#print("server_version", server_version)
#client_version = conn.client_info
#print("client_version", client_version)  # 3.0.0.0

conn.close()