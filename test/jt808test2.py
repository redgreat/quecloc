from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor, task, defer
import struct

from twisted.python import log
import sys
import time
import redis
log.startLogging(sys.stdout)



# 返回一个redis链接
def redis_conn():
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 4
    pool = redis.ConnectionPool(db=REDIS_DB, host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    r = redis.Redis(connection_pool=pool)

    return r

redis_store = redis_conn()


@defer.inlineCallbacks
def check_token(phone_number, token):
    '''
    @
    '''
    token_in_redis = yield redis_store.hget('user:%s' % phone_number, 'token')

    if token_in_redis != token:
        defer.returnValue(False)
    else:
        defer.returnValue(True)



class JT808Server(Protocol):


    def __init__(self):

        self.cid_func_dict = {
            1:self.handle_verify,
            2:self.handle_chat,
            3:self.handle_heartbeat
        }
        self.phone_number = ''
        self.state = "VERIFY"
        self.version = 0
        self.last_heartbeat_time = 0
        self._data_buffer = bytes()


    def connectionMade(self):
        '''
        @链接断开处理事件
        @Client在线数 +1，并添加至用户集合中
        '''
        self.factory.clientNumbers = self.factory.clientNumbers + 1
        log.msg('Current user nums::' , self.factory.clientNumbers)


    def connectionLost(self, reson):
        '''
        @链接断开处理事件
        @Client在线数 -1，并删除用户集合中用户
        '''
        self.factory.clientNumbers = self.factory.clientNumbers - 1
        if self.phone_number in self.factory.clients_dict:
            del self.factory.clients_dict[self.phone_number]
        log.msg('Current user nums::' , self.factory.clientNumbers)


    def dataReceived(self, data):
        '''
        @数据包接收处理事件
        '''
        self._data_buffer += data

        while True:
            cid,length,self.version = struct.unpack('>3I', data[:12])
            if length > len(self._data_buffer):
                break

            content = data[12:length]
            if cid not in self.cid_func_dict:
                return

            if self.state == 'VERIFY' and cid == 1:
                self.handle_verify(content)
            else:
                self.handle_data(cid, content)

            self._data_buffer = self._data_buffer[length:]

            if len(self._data_buffer) < 12:
                break


    @defer.inlineCallbacks
    def handle_verify(self, content):
        pass
        '''
        @鉴权包应答
        '''
        command_id = 101
        content = json.loads(content.decode('utf-8'))
        phone_number = content.get('phone_number')
        token = content.get('token')
        result = yield check_token(phone_number, token)     #异步返回 True  False

        if not result:
            send_content = json.loads({'code': 0})
            self.send_content(send_content, command_id, [phone_number])
            length = 12 + len(send_content)
            version = self.version
            header = [length, version, command_id]
            header_pack = struct.pack('>3I', *header)
            self.transport.write(header + send_content.encode('utf-8'))

        if phone_number in self.factory.clients_dict:
            log.msg('phone_number:<%s> exist' % phone_number)
            self.factory.clients_dict[phone_number].connectionLost('')
            self.factory.clients_dict.pop(phone_number)

        log.msg('welcome:%s!' % phone_number)
        self.phone_number = phone_number
        self.factory.clients_dict[phone_number] = self
        self.state = 'DATA'

        content = json.dumps({'code': 1})
        self.send_data(content, 101, [phone_number])


    def handle_data(self, cid, content):
        '''
        @句柄映射调用
        '''
        self.cid_func_dict[cid](content)


    def handle_chat(self, content):
        '''
        @聊天包应答
        '''
        content = json.loads(content.decode('utf-8'))
        ch_to = content.get('ch_to')
        ch_from = content.get('ch_from')
        ch_content = content.get('ch_content')
        content = json.dumps(dict(ch_from=ch_from, ch_content=ch_content))
        self.send_data(content, 102, [ch_to])


    def handle_heartbeat(self, content):
        '''
        @心跳包应答
        '''
        self.last_heartbeat_time = int(time.time())

        cid = 103
        length = 12
        version = self.version
        header = [cid, length, version]
        header_pack = struct.pack('>3I', *header)
        self.transport.write(header_pack)


    def send_data(self, content, cid, phone_numbers):
        '''
        @具体实现发送数据函数
        @只发送给号码在线的用户
        '''
        cid = cid
        length = 12 + len(content)
        version = self.version
        header = [cid, length, version]
        header_pack = struct.pack('>3I', *header)
        content_pack = content.encode('utf-8')

        for phone_number in phone_numbers:
            if phone_number in self.factory.clients_dict:
                self.factory.clients_dict[phone_number].transport.write(header_pack + content_pack)
                log.msg('phone_number[%s] : onlined' % phone_number)
                # log.msg(b'Server send:' + header_pack + content_pack)
            else:
                log.msg('phone_number:%s not onlined' % phone_number)



class ChatFactory(Factory):

    def __init__(self, addr=None):
        #client计数功能
        self.clientNumbers = 0
        self.clients_dict = {}
        self.p = JT808Server()


    def startFactory(self):
        log.msg('Current user nums:' , self.clientNumbers)

    def buildProtocol(self, addr):
        return self.p


    def check_clients_online(self):
        for k, v in self.clients_dict.items():
            if v.last_heartbeat_time != 0 and int(time.time()) - v.last_heartbeat_time > 8:
                log.msg('Not heartbeat:[%s]-disconnected' % k.encode('utf-8'))
                v.transport.abortConnection()
            else:
                log.msg('Found heartbeat:[%s]' % k.encode('utf-8'))



def main():

    cf = ChatFactory()
    check_online_task = task.LoopingCall(cf.check_clients_online)
    check_online_task.start(4, now=False)

    reactor.listenTCP(7707, cf)
    reactor.run()


if __name__ == '__main__':
    #
    main()