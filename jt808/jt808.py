# usr/bin/env python
# conding:utf-8

import asyncore
import json
import datetime
from jt808_core import *
from data_save import DataHandler
from msg_send import MsgHandler

class Jt808Handler(asyncore.dispatcher_with_send):

    buffer_data = {}
    def pre_handle(self, datas):
        data_handled = []
        if datas.startswith(b'~') and datas.endswith(b'~'):
            datas = datas.split(b'~')
            datas.pop()
            for data in datas:
                if data != b'':
                    data = b'~' + data + b'~'
                    data_handled.append(data)
            return data_handled
        else:
            return 'buffer_data'

    def handle_read(self):
        serv_receive = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = self.recv(8192)
        data = self.pre_handle(data)
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
                #print(response)
                if save == 'yes':
                    #拆分多条信息打包上传
                    column_res=[]
                    if res.get('all_loca')==None:
                        # 单条位置信息
                        column_res.append(res)
                    else:
                        # 多条位置信息打包上传
                        column_res=res['all_loca']

                    #循环处理数据
                    for single_res in column_res:

                        #print(single_res)
                        #消息发送
                        if single_res.get('alarm') != '[]' and single_res.get('alarm') != None:
                            content_msg = single_res.get('alarm')
                            msg_send(single_res.get('device_id'), single_res.get('dev_upload'), content_msg)

                        #定位等信息存储
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
                        sql = """REPLACE INTO `carlocdaily`(dev_upload,device_id,lat,lng,dirct,speed,mileage,hight,gnss_num,rssi,serv_receive) \
                        VALUES(\'{}\',\'{}\',{},{},{},{},{},{},{},{},\'{}\');""".format(dev_upload,
                          device_id,lat,lng,dirct,speed,mileage,hight,gnss_num,rssi,serv_receive)
                        mysql_save(mysql_pool, sql)

                if response!=b'0':
                    self.send(response)

class Jt808Server(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        print('Incoming connection from %s' % repr(addr))
        handler = Jt808Handler(sock)

if __name__ == '__main__':
    mysql_pool = DataHandler.mysql_pool_create()
    mysql_save = DataHandler.mysql_save
    msg_send = MsgHandler().send_multi_wx808_msg
    server = Jt808Server('localhost', 8080)
    asyncore.loop()
