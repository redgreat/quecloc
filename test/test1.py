import paho.mqtt.client as mqtt
import json
import pymysql

MQTTHOST = "192.168.43.188"
MQTTPORT = 1883
mqttClient = mqtt.Client()
subscribe = "esp/test"


# MySQL保存
def sqlsave(jsonData):
    # 打开数据库连接
    db = pymysql.connect(host="192.168.174.128", user="root", password="password", database="test", charset='utf8')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 插入语句
    sql = "INSERT INTO data_voice_sensor (get_time,sensorType,device,get_data,get_value) \
        VALUES ('%s','%s','%s','%s','%s');" \
          % (jsonData['get_time'], jsonData['sensorType'], jsonData['get_data'], jsonData['device'],
             jsonData['get_value'],)
    cursor.execute(sql)
    db.commit()
    print("数据库保存成功！")
    # 关闭数据库连接
    db.close()


# 连接MQTT服务器
def on_mqtt_connect():
    mqttClient = mqtt.Client("pythontest")
    mqttClient.connect(MQTTHOST, MQTTPORT, 60)
    mqttClient.loop_start()


def on_message_come(lient, userdata, msg):
    get_data = msg.payload  # bytes  b'[s]
    print(get_data)

    string = get_data.decode()  # string
    print(string)
    msgjson = json.loads(string)
    print(msgjson)
    sqlsave(msgjson)


# subscribe 消息
def on_subscribe():
    mqttClient.subscribe(subscribe, qos=0)
    mqttClient.on_message = on_message_come  # 消息到来处理函数


def main():
    on_mqtt_connect()
    while True:
        on_subscribe()


if __name__ == '__main__':
    main()
