# -*- coding:utf-8 -*-
import os
import ibm_db
import riak

# riak
#创建连接
myClient = riak.RiakClient(protocol='http', host='127.0.0.1', http_port=8098)

#创建Bucket
myBucket = myClient.bucket('test')

#写入值
val1 = 1
key1 = myBucket.new('one', data=val1)
key1.store()
val2 = "two"
key2 = myBucket.new('two', data=val2)
key2.store()
val3 = {"myValue": 3}
key3 = myBucket.new('three', data=val3)
key3.store()

#查询
fetched1 = myBucket.get('one')
fetched2 = myBucket.get('two')
fetched3 = myBucket.get('three')

assert val1 == fetched1.data
assert val2 == fetched2.data
assert val3 == fetched3.data

#更新
fetched3.data["myValue"] = 42
fetched3.store()

#删除
fetched1.delete()
fetched2.delete()
fetched3.delete()

#判断是否存在
assert myBucket.get('one').exists == False
assert myBucket.get('two').exists == False
assert myBucket.get('three').exists == False

#
bucket.enable_search()
bucket.new("one", data={'value':'one'},
           content_type="application/json").store()

bucket.search('value=one')

# 数据库连接信息
db_url = "DATABASE=wangcw;SCHEMA=db2wong;HOSTNAME=nas.wongcw.cn;PORT=50000;PROTOCOL=TCPIP;UID=db2wong;PWD=Mm19890425;"

tab_name = HUBWONG

# 查询sql
select_sql = """select * from %s""" % (tab_name)

# 连接数据库执行sql获取数据
try:
    # 连接数据库
    conn = ibm_db.connect(db_url, "", "")
    # 关闭自动提交
    ibm_db.autocommit(conn, ibm_db.SQL_AUTOCOMMIT_OFF)
    # 执行SQL语句
    stmt = ibm_db.exec_immediate(conn, select_sql)
    res = ibm_db.fetch_assoc(stmt)
    # res=ibm_db.fetch_both(stmt)
    # res = ibm_db.fetch_tuple(stmt)
    # 计数器
    num = 0
    while (res):
        num += 1
        print("第" + str(num) + "行")
        # print(res)
        # for key,item in res:
        # print()
        key = ','.join(str(k) for k in res.keys())
        val = ','.join(
            '\'' + str(v) + '\''
            if isinstance(v, str)
            # or isinstance(v,unicode)
            # or isinstance(v,datetime.datetime)
            else str(v)
            for v in res.values())
        # print(key)
        # print(val)
        ins_str = "insert into %s (%s) values (%s);" % (tab_name, key, val)
        with open(file_name, 'a') as file:
            file.write(ins_str + "\n")
        file.close()
        # res=ibm_db.fetch_tuple(stmt)
        # res = ibm_db.fetch_both(stmt)
        res = ibm_db.fetch_assoc(stmt)
    print(("%s生成完成, 共%s条数据") % (tab_name, num))
    # 提交事务
    ibm_db.commit(conn)
except Exception as e:
    # 回滚事务
    print(e)
    ibm_db.rollback(conn)
finally:
    # 关闭数据库连接
    ibm_db.close(conn)
