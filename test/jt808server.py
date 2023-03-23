#usr/bin/env python
#conding:utf-8
# JT808设备消息监听、处理、存储
# oldk 2021.6.08
import asyncore
import shelve
from jt808_analysis import *

class Jt808Handler(asyncore.dispatcher_with_send):
    buffer_data={}
    # 预处理，丢弃不完整的数据包
    def pre_handle(self,datas):
        data_handled=[]
        if datas.startswith(b'~') and datas.endswith(b'~'):
            datas=datas.split(b'~')
            datas.pop()
            for data in datas:
                if data!=b'':
                    data=b'~'+data+b'~'
                    data_handled.append(data)
            return data_handled
        else:
            return 'buffer_data'

    # 存储功能
    def handle_save(sefl,data):
        handle_data=[]
        if data.get('all_loca')==None:
            # 单条位置信息
            handle_data.append(data)
        else:
            # 多条位置信息打包上传
            handle_data=res['all_loca']

        for res in handle_data:
            with shelve.open('device') as db:
                device=db.get(res['device_id'],{})
                device['dynamic']=res
                device['device_id']=res.get('device_id')
                lng=res.get('lng','0')
                lat=res.get('lat','0')
                if lng!='0' and lat!='0':
                    device['lng']=lng
                    device['lat']=lat
                db[res['device_id']]=device
            with shelve.open(res['device_id']) as db:
                data_id=int(db.get('id','0'))+1
                db[str(data_id)] = res
                db['id']=str(data_id)

    # 数据解析，存储，回复
    def handle_read(self):
        # print(self.buffer_data)
        serv_receive=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = self.recv(8192)
        # print(data)
        data=self.pre_handle(data)
        if data!='buffer_data':
            # print(data)
            for d in data:
                dev_id=self.buffer_data.get(str(self.addr),'0')
                res=jt808_analysis(d,serv_receive,dev_id)
                # print(res)
                if res.get('device_id')!=None:
                    self.buffer_data[res['device_id']]=self
                    self.buffer_data[str(self.addr)]=res['device_id']
                else:
                    res['device_id']=self.buffer_data[str(self.addr)]

                save=res.pop('save_kind')
                response=res.pop('response')

                if save=='yes':
                    self.handle_save(res)

                if response!=b'0':
                    self.send(response)
# 设备链接监听
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
    server = Jt808Server('localhost', 8080)
    asyncore.loop()