# usr/bin/env python
# conding:utf-8
# 主入口服务

import asyncio
import json
import datetime
from jt808_core import *
#from data_save import DataHandler
from datalchemy_save import *
from msg_send import MsgHandler

class Jt808Protocol(asyncio.Protocol):
    def __init__(self):
        self.peer_addr = None  # 存储客户端IP和端口
        self.buffer_data = {}  # 存储设备ID和对应的连接
        self.mysql_pool = DataHandler.mysql_pool_create()  # 创建数据库连接池
        self.mysql_save = DataHandler.mysql_save           # 创建消息存储实例
        self.msg_send = MsgHandler().send_multi_wx808_msg  # 创建消息送实例

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0]
        port = peername[1]
        print(f'Connected by {ip}:{port}')
        self.peer_addr = peername
        # TODO 将连接信息写入配置数据库
    def data_received(self, data):
        buffer_data = {}
        data_handled = []
        if data.startswith(b'~') and data.endswith(b'~'):
            data = datas.split(b'~')
            data.pop()
            for datas in data:
                if datas != b'':
                    datas = b'~' + data + b'~'
                    data_handled.append(datas)
            return data_handled
        else:
            return 'buffer_data'
    def handle_read(self):
        serv_receive = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = self.recv(8192)
        data = self.data_received(data)
        if data != 'buffer_data':
            for d in data:
                dev_id = self.buffer_data.get(str(self.addr), '0')
                res = jt808_analysis(d, serv_receive, dev_id)
                if res.get('device_id') != None:
                    self.buffer_data[res['device_id']] = self
                    self.buffer_data[str(self.addr)] = res['device_id']
                else:
                    res['device_id'] = self.buffer_data[str(self.addr)]
                save = res.pop('save_kind')
                response = res.pop('response')
                if save == 'yes':
                    column_res=[]
                    if res.get('all_loca')==None:
                        column_res.append(res)
                    else:
                        column_res=res['all_loca']
                    for single_res in column_res:
                        if single_res.get('alarm') != '[]' and single_res.get('alarm') != None:
                            content_msg = single_res.get('alarm')
                            for alarm in res['alarm']:   # 循环发送报警信息
                                msg_send(dev_id, dev_upload, alarm)
                    #msg_send(single_res.get('device_id'), single_res.get('dev_upload'), content_msg)

                        dev_upload = single_res.get('dev_upload')
                        device_id = single_res.get('device_id')
                        lat = single_res.get('lat')
                        lng = single_res.get('lng')
                        dirct = single_res.get('dirct') or 0
                        speed = single_res.get('speed') or 0
                        mileage = single_res.get('mileage') or 0
                        hight = single_res.get('hight') or 0
                        gnss_num = single_res.get('gnss_num') or 0
                        rssi = single_res.get('rssi') or 0
                        serv_receive = single_res.get('serv_receive')
                        if lat>0 and lng>0:
                            sql = """
                            REPLACE INTO `carlocdaily`(dev_upload,device_id,lat,lng,dirct,speed,mileage,hight,gnss_num,rssi,serv_receive) \
                            VALUES(\'{}\',\'{}\',{},{},{},{},{},{},{},{},\'{}\');""".format(dev_upload,device_id,lat,lng,dirct,speed,mileage,hight,gnss_num,rssi,serv_receive)
                            #mysql_save(mysql_pool, sql)

                if response!=b'0':
                    transport.write(response)
    def connection_lost(self, exc):
        print(f'Disconnected from {self.peer_addr}')

        # 发送终端离线预警
        alert.send_offline_alert(self.peer_addr[0])

        # 更新终端连接状态
        terminal_state[self.peer_addr[0]] = 'offline'

        # 启动重连定时器
        loop = asyncio.get_event_loop()
        loop.call_later(RECONNECT_DELAY, self.reconnect)
    def reconnect(self):
        # 创建连接的回调方法
        self.callback = loop.call_later(RECONNECT_DELAY, self.reconnect)
        loop.create_connection(Jt808Protocol, HOST, PORT)

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(asyncio.start_server(Jt808Protocol, '0.0.0.0', 8080))
    print('Server started!')

    loop.run_forever()