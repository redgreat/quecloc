# usr/bin/env python
# conding:utf-8
# 消息发送接口，微信自定义菜单中可直接调用使用，返回设备终端返回值
import socket

# 服务端IP和端口
host = '127.0.0.1'
port = 7891
# 实际需要从数据库中读取

# 创建socket连接
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

# 构造JT/T808协议数据包
cmd = 'AT+CSQ'  # AT指令
data = {
    'start': 0x78,   # 数据包起始符
    'length': len(cmd) + 6, # 数据包长度
    'seq': 0x01,     # 序列号
    'cmd': 0x28,     # AT指令类型
    'content': cmd # AT指令内容
}

# 转换为二进制发送
send_data = ''
send_data += chr(data['start'])
send_data += chr(data['length'] // 256)
send_data += chr(data['length'] % 256)
send_data += chr(data['seq'])
send_data += chr(data['cmd'])
send_data += data['content']

# 发送数据
client.send(send_data.encode('gb2312'))

# 接收返回数据
recv_data = client.recv(2048)

# 解析返回数据并打印终端信号强度
start = ord(recv_data[0:1].decode('gb2312'))
length = ord(recv_data[1:2].decode('gb2312')) * 256 + ord(recv_data[2:3].decode('gb2312'))

rssi = ord(recv_data[-2:].decode('gb2312')) - 256
print('终端信号强度:', rssi)

# 关闭连接
client.close()