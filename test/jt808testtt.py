#usr/bin/env python
#conding:utf-8

import asyncore
import ctypes
import re
import time
import logging

MESSAGE_TABLE = '''
1 终端通用应答 0x0001 
2 平台通用应答 0x8001 
3 终端心跳 0x0002 
4 补传分包请求 0x8003 
5 终端注册 0x0100 
6 终端注册应答 0x8100 
7 终端注销 0x0003 
8 终端鉴权 0x0102 
9 设置终端参数 0x8103 
10 查询终端参数 0x8104 
11 查询终端参数应答 0x0104 
12 终端控制 0x8105 
13 查询指定终端参数 0x8106 
14 查询终端属性 0x8107 
15 查询终端属性应答 0x0107 
16 下发终端升级包 0x8108 
17 终端升级结果通知 0x0108 
18 位置信息汇报 0x0200 
19 位置信息查询 0x8201 
20 位置信息查询应答 0x0201 
21 临时位置跟踪控制 0x8202 
22 人工确认报警消息 0x8203 
23 文本信息下发 0x8300 
24 事件设置 0x8301
25 事件报告 0x0301
26 提问下发 0x8302
27 提问应答 0x0302
28 信息点播菜单设置 0x8303
29 信息点播/取消 0x0303
30 信息服务 0x8304
31 电话回拨 0x8400
32 设置电话本 0x8401
33 车辆控制 0x8500
34 车辆控制应答 0x0500
35 设置圆形区域 0x8600
36 删除圆形区域 0x8601
37 设置矩形区域 0x8602
38 删除矩形区域 0x8603
39 设置多边形区域 0x8604
40 删除多边形区域 0x8605
41 设置路线 0x8606
42 删除路线 0x8607
43 行驶记录仪数据采集命令 0x8700
44 行驶记录仪数据上传 0x0700
45 行驶记录仪参数下传命令 0x8701
46 电子运单上报 0x070155
47 驾驶员身份信息采集上报 0x0702 
48 上报驾驶员身份信息请求 0x8702 
49 定位数据批量上传 0x0704 
50 CAN 总线数据上传 0x0705 
51 多媒体事件信息上传 0x0800 
52 多媒体数据上传 0x0801 
53 多媒体数据上传应答 0x8800 
54 摄像头立即拍摄命令 0x8801 
55 摄像头立即拍摄命令应答 0x0805 
56 存储多媒体数据检索 0x8802
57 存储多媒体数据检索应答 0x0802
58 存储多媒体数据上传 0x8803
59 录音开始命令 0x8804
60 单条存储多媒体数据检索上传命令 0x8805
61 数据下行透传 0x8900
62 数据上行透传 0x0900
63 数据压缩上报 0x0901
64 平台RSA公钥 0x8A00
65 终端RSA公钥 0x0A00
'''
# 66 平台下行消息保留 0x8F00~0x8FFF
# 67 终端上行消息保留 0x0F00~0x0FFF

ALARM_TABLE = '''
0 1:紧急报警 收到应答后清零
1 1:超速报警 
2 1:疲劳驾驶 
3 1:危险预警 收到应答后清零
4 1:GNSS模块发生故障 
5 1:GNSS天线未接或被剪断 
6 1:GNSS天线短路 
7 1:终端主电源欠压 
8 1:终端主电源掉电 
9 1:终端LCD或显示器故障 
10 1:TTS模块故障 
11 1:摄像头故障 
12 1:道路运输证IC卡模块故障 
13 1:超速预警 
14 1:疲劳驾驶预警 
15 1:拆卸报警 
18 1:当天累计驾驶超时 
19 1:超时停车 
20 1:进出区域 收到应答后清零
21 1:进出路线 收到应答后清零
22 1:路段行驶时间不足/过长 收到应答后清零
23 1:路线偏离报警 
24 1:车辆VSS故障 
25 1:车辆油量异常 
26 1:车辆被盗 
27 1:车辆非法点火 收到应答后清零
28 1:车辆非法位移 收到应答后清零
29 1:碰撞预警 
30 1:侧翻预警 
31 1:非法开门报警
'''

STATE_TABLE = '''
    0 0:ACC关; 1:ACC开
    1 0:未定位; 1:已定位
    2 0:北纬; 1:南纬
    3 0:东经; 1:西经
    4 0:运营状态; 1:停运状态
    5 0:经纬度未经保密插件加密; 1:经纬度已经保密插件加密
    6-7 保留
    8-9 00:空车; 01:半载; 10:保留; 11:满载
    10 0:车辆油路正常; 1:车辆油路断开
    11 0:车辆电路正常; 1:车辆电路断开
    12 0:车门解锁; 1:车门加锁
    13 0:门1关; 1:门1开（前门）
    14 0:门2关; 1:门2开（中门）
    15 0:门3关; 1:门3开（后门）
    16 0:门4关; 1:门4开（驾驶席门）
    17 0:门5关; 1:门5开（自定义）
    18 0:未使用GPS卫星进行定位; 1:使用GPS
    19 0:未使用北斗卫星进行定位; 1:使用北斗
    20 0:未使用GLONASS卫星进行定位; 1:使用GLONASS
    21 0:未使用Galileo卫星进行定位; 1:使用Galileo
    22-31 保留
    '''

"""
    数据类型 描述及要求
    BYTE 无符号单字节整型（字节，8 位）
    WORD 无符号双字节整型（字，16 位）
    DWORD 无符号四字节整型（双字，32 位）
    BYTE[n] n 字节
    BCD[n] 8421 码，n 字节
    STRING GBK 编码，若无数据，置空
"""


def WORD2U16(data):
    return (data[0] << 8) | data[1]


def WORD2I16(data):
    return ctypes.c_short(WORD2U16(data)).value


def DWORD2U32(data):
    return (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]


def DWORD2I32(data):
    return ctypes.c_short(DWORD2U32(data)).value


def BCD2String(data):
    ss = ''
    for b in data:
        ss = ss + '%02X' % b
    return ss


def Byte2String(data):
    return data.decode('ascii')


def Hex2String(data):
    ret = ''
    for i in range(len(data)):
        ret = ret + '%02X' % data[i]
    return ret


class JT808Parser(object):
    def __init__(self):
        self.cnt0200 = 0
        logger = logging.getLogger('<'+self.__class__.__name__+'>')
        self.LOGI = logger.info
        self.LOGD = logger.debug
        self.LOGW = logger.warning
        self.LOGE = logger.error
        self.__InitAlarmTabel__()
        self.__InitStateTable__()
        self.__InitMessageTabel__()
        self.handleDict = {
            0x0001: self.Parse0001,  # 1 终端通用应答
            0x8001: self.Parse8001,  # 2 平台通用应答 0x8001
            0x0002: self.Parse0002,  # 3 终端心跳 0x0002
            0x8003: self.ParseNone,  # 4 补传分包请求 0x8003
            0x0100: self.Parse0100,  # 5 终端注册 0x0100
            0x8100: self.Parse8100,  # 6 终端注册应答 0x8100
            0x0003: self.ParseNone,  # 7 终端注销 0x0003
            0x0102: self.Parse0102,  # 8 终端鉴权 0x0102
            0x8103: self.ParseNone,  # 9 设置终端参数 0x8103
            0x8104: self.ParseNone,  # 10 查询终端参数 0x8104
            0x0104: self.ParseNone,  # 11 查询终端参数应答 0x0104
            0x8105: self.ParseNone,  # 12 终端控制 0x8105
            0x8106: self.ParseNone,  # 13 查询指定终端参数 0x8106
            0x8107: self.Parse8107,  # 14 查询终端属性 0x8107
            0x0107: self.Parse0107,  # 15 查询终端属性应答 0x0107
            0x8108: self.Parse8108,  # 16 下发终端升级包 0x8108
            0x0108: self.Parse0108,  # 17 终端升级结果通知 0x0108
            0x0200: self.Parse0200,  # 18 位置信息汇报 0x0200
            0x8201: self.ParseNone,  # 19 位置信息查询 0x8201
            0x0201: self.ParseNone,  # 20 位置信息查询应答 0x0201
            0x8202: self.ParseNone,  # 21 临时位置跟踪控制 0x8202
            0x8203: self.ParseNone,  # 22 人工确认报警消息 0x8203
            0x8300: self.ParseNone,  # 23 文本信息下发 0x8300
            0x8301: self.ParseNone,  # 24 事件设置 0x8301
            0x0301: self.ParseNone,  # 25 事件报告 0x0301
            0x8302: self.ParseNone,  # 26 提问下发 0x8302
            0x0302: self.ParseNone,  # 27 提问应答 0x0302
            0x8303: self.ParseNone,  # 28 信息点播菜单设置 0x8303
            0x0303: self.ParseNone,  # 29 信息点播/取消 0x0303
            0x8304: self.ParseNone,  # 30 信息服务
            0x8400: self.ParseNone,  # 31 电话回拨
            0x8401: self.ParseNone,  # 32 设置电话本
            0x8500: self.ParseNone,  # 33 车辆控制
            0x0500: self.ParseNone,  # 34 车辆控制应答
            0x8600: self.ParseNone,  # 35 设置圆形区域
            0x8601: self.ParseNone,  # 36 删除圆形区域
            0x8602: self.ParseNone,  # 37 设置矩形区域
            0x8603: self.ParseNone,  # 38 删除矩形区域
            0x8604: self.ParseNone,  # 39 设置多边形区域
            0x8605: self.ParseNone,  # 40 删除多边形区域
            0x8606: self.ParseNone,  # 41 设置路线
            0x8607: self.ParseNone,  # 42 删除路线
            0x8700: self.ParseNone,  # 43 行驶记录仪数据采集命令
            0x0700: self.ParseNone,  # 44 行驶记录仪数据上传
            0x8701: self.ParseNone,  # 45 行驶记录仪参数下传命令
            0x0701: self.ParseNone,  # 46 电子运单上报
            0x0702: self.ParseNone,  # 47 驾驶员身份信息采集上报
            0x8702: self.ParseNone,  # 48 上报驾驶员身份信息请求
            0x0704: self.ParseNone,  # 49 定位数据批量上传
            0x0705: self.ParseNone,  # 50 CAN 总线数据上传
            0x0800: self.ParseNone,  # 51 多媒体事件信息上传
            0x0801: self.ParseNone,  # 52 多媒体数据上传
            0x8800: self.ParseNone,  # 53 多媒体数据上传应答
            0x8801: self.ParseNone,  # 54 摄像头立即拍摄命令
            0x0805: self.ParseNone,  # 55 摄像头立即拍摄命令应答
            0x8802: self.ParseNone,  # 56 存储多媒体数据检索
            0x0802: self.ParseNone,  # 57 存储多媒体数据检索应答
            0x8803: self.ParseNone,  # 58 存储多媒体数据上传
            0x8804: self.ParseNone,  # 59 录音开始命令
            0x8805: self.ParseNone,  # 60 单条存储多媒体数据检索上传命令
            0x8900: self.ParseNone,  # 61 数据下行透传
            0x0900: self.ParseNone,  # 62 数据上行透传
            0x0901: self.ParseNone,  # 63 数据压缩上报
            0x8A00: self.ParseNone,  # 64 平台RSA公钥
            0x0A00: self.ParseNone,  # 65 终端RSA公钥
        }
        self.lastData = None

    def ParseHeader(self, data):
        if None == data:
            return None

        if len(data) < 12:
            self.LOGE("data len(%d) < 12: %s" %
                      (len(data), self.BytesLog(data)))
            return None

        header = dict()
        try:
            header["MsgId"] = WORD2U16(data[:2])
            header["Attr"] = WORD2U16(data[2:4])
            header["Length"] = header["Attr"] & 0x3FF  # bit0~bit9
            header["DevNum"] = BCD2String(data[4:10])
            header["SeqNo"] = WORD2U16(data[10:12])
        except Exception as e:
            self.LOGE(str(e))
            return None
        return header

    def ParseNone(self, data):
        return None

    def Parse0001(self, data):
        resultTable = {0: "成功", 1: "失败", 2: "消息有误", 3: "不支持"}
        body = dict()
        body["AckSeq"] = WORD2U16(data[:2])
        body["AckId"] = WORD2U16(data[2:4])
        body["Result"] = data[4]
        body["ResultText"] = resultTable.get(body["Result"], "*")
        return body

    def Parse8001(self, data):
        if len(data) < 5:
            return None
        resultTable = {0: "成功", 1: "失败", 2: "消息有误", 3: "不支持", 4: "报警处理确认"}
        body = dict()
        body["AckSeq"] = WORD2U16(data[:2])
        body["AckId"] = WORD2U16(data[2:4])
        body["Result"] = data[4]
        body["ResultText"] = resultTable.get(body["Result"], "*")
        return body

    def Parse0002(self, data):
        # 终端心跳数据消息体为空
        return None

    def Parse0100(self, data):
        body = dict()
        body["ProvinceId"] = WORD2U16(data[:2])
        body["CityId"] = WORD2U16(data[2:4])
        body["ManufacturerId"] = Byte2String(data[4:9])
        body["DevModel"] = Byte2String(data[9:29])
        body["DevId"] = Byte2String(data[29:36])
        body["ColorOfCar"] = data[36]
        body["SignOfCar"] = Byte2String(data[37:])
        return body

    def Parse8100(self, data):
        resultTable = {0: "成功",
                       1: "车辆已被注册",
                       2: "数据库中无该车辆",
                       3: "终端已被注册",
                       4: "数据库中无该终端"}
        body = dict()
        body["AckSeq"] = WORD2U16(data[:2])
        body["Result"] = data[2]
        body["ResultText"] = resultTable.get(body["Result"], "**")
        if 0 == body["Result"]:
            body["AuthCode"] = Byte2String(data[3:])
        return body

    def Parse0102(self, data):
        body = dict()
        body['AuthCode'] = Byte2String(data)
        return body

    def Parse8107(self, data):
        # 消息 ID： 0x8107
        # 查询终端属性消息体为空
        return None

    def Parse0107(self, data):
        body = dict()
        # 0 终端类型 WORD
        body['DevType'] = (data[0] << 8) | data[1]
        # 2 制造商 ID BYTE[5] 5 个字节，终端制造商编码。
        body['ManufacturerID'] = Hex2String(data[2:7])
        # 7 终端型号 BYTE[20] 此终端型号由制造商自行定义，位数不足时，后补“0X00”
        body['Model'] = Byte2String(data[7:27])
        #body['Model'] = Hex2String(data[7:27])
        # 27 终端 ID BYTE[7] 由大写字母和数字组成，此终端 ID 由制造商自行定义，位数不足时，后补“0X00”。
        body['DevID'] = Byte2String(data[27:34])
        # 34 终端 SIM 卡 ICCID BCD[10] 终端 SIM 卡 ICCID 号
        body['ICCID'] = BCD2String(data[34:44])
        # 44 终端硬件版本号长度 BYTE
        body['HWVerLen'] = n = data[44]
        # 45 终端硬件版本号 STRING
        offset = 45
        body['HWVer'] = Byte2String(data[offset:offset+n])
        # 45+n 终端固件版本号长度 BYTE
        offset = offset + n
        body['SWVerLen'] = m = data[offset]
        # 45+n+1 终端固件版本号 STRING
        offset = offset + 1
        body['SWVer'] = Byte2String(data[offset:offset+m])
        # 45+n+1+m GNSS 模块属性
        offset = offset + m
        body['AttrGNSS'] = data[offset]
        # 45+n+1+m+1 通信模块属性
        offset = offset + 1
        body['AttrCOMM'] = data[offset]
        return body

    def Parse8108(self, data):
        body = dict()
        # 0 升级类型 BYTE
        body["Type"] = data[0]
        body["ManufacturerId"] = BCD2String(data[1:6])
        # 1 制造商 ID BYTE[5] 制造商编号

        # 6 版本号长度 BYTE n
        body["VernoLen"] = vernoLen = data[6]
        # 7 版本号 STRING
        offset = 7 + vernoLen
        body["Verno"] = Byte2String(data[7:offset])
        # 7+n 升级数据包长度 DWORD 单位为 BYTE
        body["UrlLen"] = urlLen = DWORD2U32(data[offset:offset+4])
        offset = offset + 4
        body["Url"] = Byte2String(data[offset:offset+urlLen])
        offset = offset+urlLen
        return body

    def Parse0108(self, data):
        body = dict()
        body['Type'] = data[0]
        body['Result'] = data[1]
        return body

    def Parse0200(self, data):
        # 扩展协议
        def ExtendParse(data):
            idx = 0
            extData = dict()
            while idx < len(data):
                ext_id = data[idx]
                if ext_id == 0:
                    break
                idx = idx + 1
                ext_len = data[idx]
                ext_body = data[idx + 1:]
                if ext_id == 0x30:  # 0x30 CSQ
                    if ext_len == 1:
                        extData["CSQ"] = data[idx + 1]
                    else:
                        pass
                elif ext_id == 0x31:  # 0x31 卫星数
                    if ext_len == 1:
                        extData["Sats"] = data[idx + 1]
                    else:
                        pass
                elif ext_id == 0xE1 and ext_len == 0x0A:
                    # 0xE1 Quality / HDOP
                    extData["Quality"] = data[idx + 2]
                    extData["HDOP"] = ((data[idx + 5] << 8)
                                       | data[idx + 6]) / 10

                    if (data[idx + 1] == 0x03):
                        # print("%d,%d,%d" % (data[idx+7], data[idx+8], (data[idx+9] << 8) | data[idx+10]))
                        extData["Vib10S"] = data[idx+7]
                        extData["Vib30S"] = data[idx+8]
                        extData["TTFF"] = WORD2I16(data[idx + 9:])
                    elif (data[idx + 1] == 0x02):
                        pass
                elif ext_id == 0xE4:
                    # 设备倾斜角度
                    extData["DevAngle"] = data[idx + 1]
                elif ext_id == 0xE6:
                    # 电压,百分之一伏
                    extData["Voltage"] = WORD2U16(data[idx + 1:]) / 100
                elif ext_id == 0xEE:
                    # 0xEE
                    extData["Crash"] = WORD2U16(data[idx + 1:])
                    extData["VibMins"] = WORD2U16(data[idx + 3:])
                    extData["MinZ"] = WORD2I16(data[idx + 5:])
                    extData["MaxZ"] = WORD2I16(data[idx + 7:])
                    extData["TTFF"] = WORD2I16(data[idx + 9:])
                    extData["Count"] = WORD2I16(data[idx + 11:])
                    extData["SumTime"] = DWORD2U32(data[idx + 13:])
                    # extData["CurrTime"] = DWORD2U32(data[idx + 17 : ])
                elif ext_id == 0x01:
                    if 4 == ext_len:
                        extData["Mileage"] = DWORD2U32(ext_body) / 10
                elif ext_id == 0xEF:
                    extData["LBS"] = "基站定位"
                elif ext_id == 0xE2:
                    extData['Percent'] = int(WORD2U16(ext_body) / 100)
                elif ext_id == 0xE3:
                    extData["开机时间"] = "%02X/%02X/%02X %02X:%02X:%02X" % (ext_body[0],
                                                                             ext_body[1], ext_body[2], ext_body[3], ext_body[4], ext_body[5])
                elif ext_id == 0xE5:
                    pass
                else:
                    extData["0x%02X" % ext_id] = str(ext_body)
                    self.LOGI("ext_id:0x%02x" % ext_id)

                idx = idx + 1 + ext_len

            for k in extData.keys():
                body[k] = extData[k]
            # == Extend END ===

        """
        0 报警标志 DWORD 报警标志位定义见 表 24
        4 状态 DWORD 状态位定义见 表 25
        8 纬度 DWORD 以度为单位的纬度值乘以10的6次方，精确到百万分之一度
        12 经度 DWORD 以度为单位的经度值乘以10的6次方，精确到百万分之一度
        16 高程 WORD 海拔高度，单位为米（m）
        18 速度 WORD 1/10km/h
        20 方向 WORD 0-359，正北为 0，顺时针
        21 时间 BCD[6] YY-MM-DD-hh-mm-ss（GMT+8 时间，本标准中之后涉及的时间均采用此时区
        """
        body = dict()
        alarm = DWORD2U32(data[:4])
        status = DWORD2U32(data[4:8])
        body["Latitude"] = DWORD2U32(data[8:12]) / (10 ** 6)
        body["Longitude"] = DWORD2U32(data[12:16]) / (10 ** 6)
        body["Altitude"] = WORD2I16(data[16:18])
        body["Speed"] = round(WORD2U16(data[18:20]) / 10, 1)
        body["Angle"] = WORD2U16(data[20:22])

        if data[23] > 0x12:
            self.LOGE("Invalid month(%X): " % data[23] + self.BytesLog(data))
            return None
        else:
            body["Time"] = "20%02X/%02X/%02XT%02X:%02X:%02X" % (
                data[22], data[23], data[24], data[25], data[26], data[27])

        body["Alarm"] = ("%X" % alarm, self.Parse0200Alarm(alarm))
        body["Status"] = ("%X" % status, self.Parse0200State(status))
        try:
            ExtendParse(data[28:])
        except Exception as e:
            self.LOGE("0200 ExtendParse>>" + str(e))
        return body

    def Parse0200Alarm(self, alarm):
        alarmList = []
        for bit in range(32):
            if (1 << bit) & alarm and bit in self.alarmTabel.keys():
                alarmList.append(self.alarmTabel[bit])
        return tuple(alarmList)

    def Parse0200State(self, state):
        stateList = []
        for bit in range(32):
            if (1 << bit) & state and bit in self.stateTabel.keys():
                stateList.append(self.stateTabel[bit])
        return tuple(stateList)

    def BytesLog(self, bdata=b""):
        logbuf = ""
        for b in bdata:
            logbuf = logbuf + "%02X " % b
        return logbuf

    def ParseData(self, data):
        # 转换成bytes
        def ToBytearray(data):
            ba = bytearray()
            for i in range(0, len(data), 2):
                tmp = int(data[i:i+2], 16)
                ba.append(tmp)
            return ba
        # 反转义

        def Unescape(data=b''):
            self.LOGD("data:" + str(data))
            length = data[2] << 8 | data[3]
            if 12 + length + 1 == len(data):
                self.LOGD("No escape")
            else:
                data = data.replace(b'\x7d\x02', b'\x7e')
                data = data.replace(b'\x7d\x01', b'\x7d')
            return data

        # 去空格
        buffer = data.replace(' ', '').upper()
        if buffer.startswith("7E"):
            buffer = buffer[2:]
        if buffer.endswith("7E"):
            buffer = buffer[:-2]
        if len(buffer) == 0 or len(buffer) / 2 == 1:
            self.LOGI("长度不应为0 或 单数")
            print('1',buffer)
            return None
        if buffer[0] != '0' and buffer[0] != '8':
            self.LOGI("msgid是0或8开头")
            print('2',buffer)
            return None

        try:
            buffer = ToBytearray(buffer)
            buffer = Unescape(buffer)
            print('3',buffer)
        except Exception as e:
            self.LOGE("Reverse>>" + str(e) + '|' + str(data))
            print('4',buffer)
            buffer = None
        else:
            if self.lastData == buffer:
                self.LOGI("self.lastData == buffer")
                print('5',buffer)
                return None
            self.lastData = buffer
            buffer = buffer[:-1]  # 跳过校验码

        if None == buffer:
            self.LOGI("None == buffer")
            print('6',buffer)
            return None

        offset = 0
        try:
            header = self.ParseHeader(buffer)
            print('1',ParseHeader)
        except Exception as e:
            self.LOGE(str(e))
            header = None

        if None == header:
            self.LOGE(data)
            return None

        msgId = header.get("MsgId")
        if None == msgId:
            return None

        # if msgId == 0x0200:
        #    self.cnt0200 = self.cnt0200 + 1
        #    print(self.cnt0200)
        self.LOGD("msgId:%04X" % msgId)
        handle = self.handleDict.get(msgId)
        if handle == None:
            #self.LOGW(u"未处理的消息: %04X >> %s" % (msgId, data))
            return (header, None)

        try:
            offset = 12
            body = handle(buffer[offset:])
        except Exception as e:
            body = None
            self.LOGE(data)
            self.LOGE(self.BytesLog(buffer))
            # self.LOGE(self.BytesLog(buffer[offset:]))
            self.LOGE(handle.__name__ + ">>" + str(e))
        else:
            if type(body) == type(dict()):
                temp = ''
                for b in buffer[offset:]:
                    temp = temp + '%02X ' % b
                body["BodyData"] = temp.strip()

        return (header, body)

    def ParseMultiLog(self, dataList):
        if type(dataList) in (type([]), type(())) and len(dataList) > 0:
            pass
        else:
            self.LOGE("Type Error")
            print(("Type Error"))
            return None

        retList = []
        for data in dataList:
            data = data.strip()
            try:
                retsult = self.ParseData(str(data))
                print(retsult)
            except Exception as e:
                self.LOGE("%s>>%s" % (str(e), data))
                continue

            if None == retsult or None == retsult[0]:
                continue
            msg = retsult[0]
            if len(retsult) >= 2 and None != retsult[1]:
                for k in retsult[1]:
                    msg[k] = retsult[1][k]
            retList.append(msg)
        return retList

    def __InitMessageTabel__(self):
        lines = MESSAGE_TABLE.split('\n')
        self.messageTabel = dict()
        for ln in lines:
            ln = ln.strip()
            if len(ln) == 0:
                continue
            try:
                array = ln.split(' ')
                msgid = array[2].strip()
                text = array[1]
            except:
                pass
            else:
                self.messageTabel[msgid] = text

    def __InitAlarmTabel__(self):
        lines = ALARM_TABLE.split('\n')
        self.alarmTabel = dict()
        for ln in lines:
            ln = ln.strip()
            if len(ln) == 0:
                continue
            try:
                array = ln.split(' ')
                bit = int(array[0])
                text = array[1][2:].strip()
            except Exception as e:
                self.LOGD(str(e))
            else:
                self.alarmTabel[bit] = text

    def __InitStateTable__(self):
        lines = STATE_TABLE.split('\n')
        self.stateTabel = dict()
        for ln in lines:
            ln = ln.strip()
            if len(ln) == 0:
                continue
            try:
                array = ln.split(' ')
                bit = int(array[0])
                text1 = array[2][2:].strip().strip(';')
            except Exception as e:
                self.LOGD(str(e))
            else:
                self.stateTabel[bit] = text1  # (text0, text1)

    def GetMessageComment(self, msgId):
        if type(msgId) == type(0):
            msgId = '0x%04X' % msgId
        elif type(msgId) == type(''):
            if not msgId.startswith('0x'):
                msgId = '0x' + msgId
        else:
            return None

        if msgId in self.messageTabel.keys():
            return self.messageTabel[msgId]

        return "未知ID:" + msgId

    def Extract808Log(self, buffer):
        def AppendTo(log, data):
            data = data.strip().upper()
            if '7E 7E' in data:
                aList = []
                for a in line.split('7E 7E'):
                    if not a.startswith('7E '):
                        a = '7E ' + a
                    if not a.endswith('7E'):
                        a = a + ' 7E'
                    aList.append(a)
            else:
                aList = [data]
            for a in aList:
                if re.match(r"^[0-9A-F\ ]*$", a):
                    self.LOGD(a)
                    log.append(a)
        logList = []
        logDnList = []
        for line in buffer:
            line = line.strip().upper()  # 统一大写

            if len(line) <= len("7e02007e"):
                continue

            if 'INFO - 上行:' in line or 'INFO - 下行:' in line or \
                    ("[下行]" in line or "[上行]" in line):
                line = line[line.rindex(':')+1:].strip()
                AppendTo(logDnList, line)
            elif line.startswith('{') and line.endswith('"}') and '"LOGS":' in line:
                line = line[line.rindex(':"')+2: -2].strip()
                AppendTo(logDnList, line)
            elif "hex = 7E" in line and line.endswith("7E"):
                line = line[line.rindex('=')+1:].strip().lower()
                AppendTo(logList, line)
            else:
                if not '7E' in line:
                    continue
                try:
                    idxLeft = line.index('7E')
                    idxRight = line.rindex('7E')
                except Exception as e:
                    self.LOGE(str(e))
                    continue

                if idxLeft == idxRight:
                    continue

                line = line[idxLeft:idxRight+3].strip()
                if len(line) < 12:
                    continue
                AppendTo(logList, line)

        if len(logDnList) > 0:
            self.LOGD("len(logDnList) = " + str(len(logDnList)))
            return ("DN", logDnList)
        else:
            return ("GC", logList)

    # 将0200的数据转换成kml用的位置数据
    def JT808ToLocation(self, msg=dict()):
        if msg['MsgId'] != 0x0200 or msg.get("Status") == None:
            return None
        status = int(msg["Status"][0], 16)
        if (status & 0x2) == 0:
            # 未定位
            return None

        data = dict()
        try:
            tt = time.strptime(msg['Time'], "%Y/%m/%dT%H:%M:%S")
            data['UTCTime'] = "%02d%02d%02d" % (
                tt.tm_hour, tt.tm_min, tt.tm_sec)
            if(tt.tm_year > 1900):
                data['UTCDate'] = "%02d%02d%02d" % (
                    tt.tm_mday, tt.tm_mon, tt.tm_year-1900)
            else:
                data['UTCDate'] = "%02d%02d%02d" % (
                    tt.tm_mday, tt.tm_mon, tt.tm_year)
        except Exception as e:
            self.LOGE(str(e))
            return None

        data["UTC"] = msg['Time']
        keyArray = ["Quality", "Sats", "HDOP", "Latitude",
                    "Longitude", "Altitude", "Speed", "Angle", 'Mileage']
        for key in keyArray:
            if None != msg.get(key, None):
                data[key] = msg.get(key)
        self.LOGD(str(data))
        return data

class Jt808Handler(asyncore.dispatcher_with_send):
    buffer_data={}
    def pre_handle(self, datas):
        data_handled=[]
        #print(datas)
        if datas.startswith(b'~') and datas.endswith(b'~'):
            datas=datas.split(b'~')
            datas.pop()
            for data in datas:
                if data!=b'':
                    data=bytes(b'~'+data+b'~')
                    data_handled.append(data)
            return data_handled
        else:
            return 'buffer_data'
    def handle_read(self):
        #serv_receive=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = self.recv(8192)
        # print(data)
        dataList = self.pre_handle(data)
        if data!='buffer_data':
            if len(dataList) == 0:
                return
            else:
                #print(dataList)
                #print(type(dataList))
                #print(type(dataList[0]))
                JT808 = JT808Parser()
                result = JT808.ParseMultiLog(dataList)
                #print(result)

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