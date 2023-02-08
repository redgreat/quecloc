#!/usr/bin/python
# -*- coding: utf-8 -*

import paho.mqtt.client as mqtt
import json
import pymysql
import time
def gettime():
    time1=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    return time1

# 服务器地址
host = '192.168.43.188'
# 通信端口 默认端口1883
port = 1883


username = ''
password = ''

# 订阅主题名
topic = 'esp/test'


# 连接后事件
def on_connect(client, userdata, flags, respons_code):
    if respons_code == 0:
        # 连接成功
        print('Connection Succeed!')
    else:
        # 连接失败并显示错误代码
        print('Connect Error status {0}'.format(respons_code))
    # 订阅信息
    client.subscribe(topic)


# 接收到数据后事件
def on_message(client, userdata, msg):
    # 打印订阅消息主题
    # print("topic", msg.topic)
    # 打印消息数据
    jsondata=json.loads(msg.payload)
    print("msg payload", jsondata)
    sqlsave(jsondata)

def main_demo():
    client = mqtt.Client()
    # 注册事件
    client.on_connect = on_connect
    client.on_message = on_message
    # 设置账号密码（如果需要的话）
    client.username_pw_set(username, password=password)
    # 连接到服务器
    client.connect(host, port=port, keepalive=60)
    # 守护连接状态
    client.loop_forever()

#MySQL保存
def sqlsave(jsonData):
      # 打开数据库连接
    db = pymysql.connect(host="192.168.174.128",user="root",password="password",database="test",charset='utf8')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 插入语句
    sql = "INSERT INTO data_voice (get_time,sensorType,device,get_data,get_value) \
            VALUES ('%s','%s','%s','%s','%s');"\
                %(gettime(),jsonData['sensorType'],jsonData['get_data'],jsonData['device'],jsonData['get_value'],)
    cursor.execute(sql)
    db.commit()
    print("数据库保存成功！")
    # 关闭数据库连接
    db.close()


if __name__ == '__main__':
    main_demo()



