#usr/bin/env python
#conding:utf-8

import asyncore
import ctypes
import sys
import os
import re
import csv
import time
import logging

MESSAGE_TABLE = '''
1 �ն�ͨ��Ӧ�� 0x0001 
2 ƽ̨ͨ��Ӧ�� 0x8001 
3 �ն����� 0x0002 
4 �����ְ����� 0x8003 
5 �ն�ע�� 0x0100 
6 �ն�ע��Ӧ�� 0x8100 
7 �ն�ע�� 0x0003 
8 �ն˼�Ȩ 0x0102 
9 �����ն˲��� 0x8103 
10 ��ѯ�ն˲��� 0x8104 
11 ��ѯ�ն˲���Ӧ�� 0x0104 
12 �ն˿��� 0x8105 
13 ��ѯָ���ն˲��� 0x8106 
14 ��ѯ�ն����� 0x8107 
15 ��ѯ�ն�����Ӧ�� 0x0107 
16 �·��ն������� 0x8108 
17 �ն��������֪ͨ 0x0108 
18 λ����Ϣ�㱨 0x0200 
19 λ����Ϣ��ѯ 0x8201 
20 λ����Ϣ��ѯӦ�� 0x0201 
21 ��ʱλ�ø��ٿ��� 0x8202 
22 �˹�ȷ�ϱ�����Ϣ 0x8203 
23 �ı���Ϣ�·� 0x8300 
24 �¼����� 0x8301
25 �¼����� 0x0301
26 �����·� 0x8302
27 ����Ӧ�� 0x0302
28 ��Ϣ�㲥�˵����� 0x8303
29 ��Ϣ�㲥/ȡ�� 0x0303
30 ��Ϣ���� 0x8304
31 �绰�ز� 0x8400
32 ���õ绰�� 0x8401
33 �������� 0x8500
34 ��������Ӧ�� 0x0500
35 ����Բ������ 0x8600
36 ɾ��Բ������ 0x8601
37 ���þ������� 0x8602
38 ɾ���������� 0x8603
39 ���ö�������� 0x8604
40 ɾ����������� 0x8605
41 ����·�� 0x8606
42 ɾ��·�� 0x8607
43 ��ʻ��¼�����ݲɼ����� 0x8700
44 ��ʻ��¼�������ϴ� 0x0700
45 ��ʻ��¼�ǲ����´����� 0x8701
46 �����˵��ϱ� 0x070155
47 ��ʻԱ�����Ϣ�ɼ��ϱ� 0x0702 
48 �ϱ���ʻԱ�����Ϣ���� 0x8702 
49 ��λ���������ϴ� 0x0704 
50 CAN ���������ϴ� 0x0705 
51 ��ý���¼���Ϣ�ϴ� 0x0800 
52 ��ý�������ϴ� 0x0801 
53 ��ý�������ϴ�Ӧ�� 0x8800 
54 ����ͷ������������ 0x8801 
55 ����ͷ������������Ӧ�� 0x0805 
56 �洢��ý�����ݼ��� 0x8802
57 �洢��ý�����ݼ���Ӧ�� 0x0802
58 �洢��ý�������ϴ� 0x8803
59 ¼����ʼ���� 0x8804
60 �����洢��ý�����ݼ����ϴ����� 0x8805
61 ��������͸�� 0x8900
62 ��������͸�� 0x0900
63 ����ѹ���ϱ� 0x0901
64 ƽ̨RSA��Կ 0x8A00
65 �ն�RSA��Կ 0x0A00
'''
# 66 ƽ̨������Ϣ���� 0x8F00~0x8FFF
# 67 �ն�������Ϣ���� 0x0F00~0x0FFF

ALARM_TABLE = '''
0 1:�������� �յ�Ӧ�������
1 1:���ٱ��� 
2 1:ƣ�ͼ�ʻ 
3 1:Σ��Ԥ�� �յ�Ӧ�������
4 1:GNSSģ�鷢������ 
5 1:GNSS����δ�ӻ򱻼��� 
6 1:GNSS���߶�· 
7 1:�ն�����ԴǷѹ 
8 1:�ն�����Դ���� 
9 1:�ն�LCD����ʾ������ 
10 1:TTSģ����� 
11 1:����ͷ���� 
12 1:��·����֤IC��ģ����� 
13 1:����Ԥ�� 
14 1:ƣ�ͼ�ʻԤ�� 
15 1:��ж���� 
18 1:�����ۼƼ�ʻ��ʱ 
19 1:��ʱͣ�� 
20 1:�������� �յ�Ӧ�������
21 1:����·�� �յ�Ӧ�������
22 1:·����ʻʱ�䲻��/���� �յ�Ӧ�������
23 1:·��ƫ�뱨�� 
24 1:����VSS���� 
25 1:���������쳣 
26 1:�������� 
27 1:�����Ƿ���� �յ�Ӧ�������
28 1:�����Ƿ�λ�� �յ�Ӧ�������
29 1:��ײԤ�� 
30 1:�෭Ԥ�� 
31 1:�Ƿ����ű���
'''

STATE_TABLE = '''
    0 0:ACC��; 1:ACC��
    1 0:δ��λ; 1:�Ѷ�λ
    2 0:��γ; 1:��γ
    3 0:����; 1:����
    4 0:��Ӫ״̬; 1:ͣ��״̬
    5 0:��γ��δ�����ܲ������; 1:��γ���Ѿ����ܲ������
    6-7 ����
    8-9 00:�ճ�; 01:����; 10:����; 11:����
    10 0:������·����; 1:������·�Ͽ�
    11 0:������·����; 1:������·�Ͽ�
    12 0:���Ž���; 1:���ż���
    13 0:��1��; 1:��1����ǰ�ţ�
    14 0:��2��; 1:��2�������ţ�
    15 0:��3��; 1:��3�������ţ�
    16 0:��4��; 1:��4������ʻϯ�ţ�
    17 0:��5��; 1:��5�����Զ��壩
    18 0:δʹ��GPS���ǽ��ж�λ; 1:ʹ��GPS
    19 0:δʹ�ñ������ǽ��ж�λ; 1:ʹ�ñ���
    20 0:δʹ��GLONASS���ǽ��ж�λ; 1:ʹ��GLONASS
    21 0:δʹ��Galileo���ǽ��ж�λ; 1:ʹ��Galileo
    22-31 ����
    '''

"""
    �������� ������Ҫ��
    BYTE �޷��ŵ��ֽ����ͣ��ֽڣ�8 λ��
    WORD �޷���˫�ֽ����ͣ��֣�16 λ��
    DWORD �޷������ֽ����ͣ�˫�֣�32 λ��
    BYTE[n] n �ֽ�
    BCD[n] 8421 �룬n �ֽ�
    STRING GBK ���룬�������ݣ��ÿ�
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
            0x0001: self.Parse0001,  # 1 �ն�ͨ��Ӧ��
            0x8001: self.Parse8001,  # 2 ƽ̨ͨ��Ӧ�� 0x8001
            0x0002: self.Parse0002,  # 3 �ն����� 0x0002
            0x8003: self.ParseNone,  # 4 �����ְ����� 0x8003
            0x0100: self.Parse0100,  # 5 �ն�ע�� 0x0100
            0x8100: self.Parse8100,  # 6 �ն�ע��Ӧ�� 0x8100
            0x0003: self.ParseNone,  # 7 �ն�ע�� 0x0003
            0x0102: self.Parse0102,  # 8 �ն˼�Ȩ 0x0102
            0x8103: self.ParseNone,  # 9 �����ն˲��� 0x8103
            0x8104: self.ParseNone,  # 10 ��ѯ�ն˲��� 0x8104
            0x0104: self.ParseNone,  # 11 ��ѯ�ն˲���Ӧ�� 0x0104
            0x8105: self.ParseNone,  # 12 �ն˿��� 0x8105
            0x8106: self.ParseNone,  # 13 ��ѯָ���ն˲��� 0x8106
            0x8107: self.Parse8107,  # 14 ��ѯ�ն����� 0x8107
            0x0107: self.Parse0107,  # 15 ��ѯ�ն�����Ӧ�� 0x0107
            0x8108: self.Parse8108,  # 16 �·��ն������� 0x8108
            0x0108: self.Parse0108,  # 17 �ն��������֪ͨ 0x0108
            0x0200: self.Parse0200,  # 18 λ����Ϣ�㱨 0x0200
            0x8201: self.ParseNone,  # 19 λ����Ϣ��ѯ 0x8201
            0x0201: self.ParseNone,  # 20 λ����Ϣ��ѯӦ�� 0x0201
            0x8202: self.ParseNone,  # 21 ��ʱλ�ø��ٿ��� 0x8202
            0x8203: self.ParseNone,  # 22 �˹�ȷ�ϱ�����Ϣ 0x8203
            0x8300: self.ParseNone,  # 23 �ı���Ϣ�·� 0x8300
            0x8301: self.ParseNone,  # 24 �¼����� 0x8301
            0x0301: self.ParseNone,  # 25 �¼����� 0x0301
            0x8302: self.ParseNone,  # 26 �����·� 0x8302
            0x0302: self.ParseNone,  # 27 ����Ӧ�� 0x0302
            0x8303: self.ParseNone,  # 28 ��Ϣ�㲥�˵����� 0x8303
            0x0303: self.ParseNone,  # 29 ��Ϣ�㲥/ȡ�� 0x0303
            0x8304: self.ParseNone,  # 30 ��Ϣ����
            0x8400: self.ParseNone,  # 31 �绰�ز�
            0x8401: self.ParseNone,  # 32 ���õ绰��
            0x8500: self.ParseNone,  # 33 ��������
            0x0500: self.ParseNone,  # 34 ��������Ӧ��
            0x8600: self.ParseNone,  # 35 ����Բ������
            0x8601: self.ParseNone,  # 36 ɾ��Բ������
            0x8602: self.ParseNone,  # 37 ���þ�������
            0x8603: self.ParseNone,  # 38 ɾ����������
            0x8604: self.ParseNone,  # 39 ���ö��������
            0x8605: self.ParseNone,  # 40 ɾ�����������
            0x8606: self.ParseNone,  # 41 ����·��
            0x8607: self.ParseNone,  # 42 ɾ��·��
            0x8700: self.ParseNone,  # 43 ��ʻ��¼�����ݲɼ�����
            0x0700: self.ParseNone,  # 44 ��ʻ��¼�������ϴ�
            0x8701: self.ParseNone,  # 45 ��ʻ��¼�ǲ����´�����
            0x0701: self.ParseNone,  # 46 �����˵��ϱ�
            0x0702: self.ParseNone,  # 47 ��ʻԱ�����Ϣ�ɼ��ϱ�
            0x8702: self.ParseNone,  # 48 �ϱ���ʻԱ�����Ϣ����
            0x0704: self.ParseNone,  # 49 ��λ���������ϴ�
            0x0705: self.ParseNone,  # 50 CAN ���������ϴ�
            0x0800: self.ParseNone,  # 51 ��ý���¼���Ϣ�ϴ�
            0x0801: self.ParseNone,  # 52 ��ý�������ϴ�
            0x8800: self.ParseNone,  # 53 ��ý�������ϴ�Ӧ��
            0x8801: self.ParseNone,  # 54 ����ͷ������������
            0x0805: self.ParseNone,  # 55 ����ͷ������������Ӧ��
            0x8802: self.ParseNone,  # 56 �洢��ý�����ݼ���
            0x0802: self.ParseNone,  # 57 �洢��ý�����ݼ���Ӧ��
            0x8803: self.ParseNone,  # 58 �洢��ý�������ϴ�
            0x8804: self.ParseNone,  # 59 ¼����ʼ����
            0x8805: self.ParseNone,  # 60 �����洢��ý�����ݼ����ϴ�����
            0x8900: self.ParseNone,  # 61 ��������͸��
            0x0900: self.ParseNone,  # 62 ��������͸��
            0x0901: self.ParseNone,  # 63 ����ѹ���ϱ�
            0x8A00: self.ParseNone,  # 64 ƽ̨RSA��Կ
            0x0A00: self.ParseNone,  # 65 �ն�RSA��Կ
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
        resultTable = {0: "�ɹ�", 1: "ʧ��", 2: "��Ϣ����", 3: "��֧��"}
        body = dict()
        body["AckSeq"] = WORD2U16(data[:2])
        body["AckId"] = WORD2U16(data[2:4])
        body["Result"] = data[4]
        body["ResultText"] = resultTable.get(body["Result"], "*")
        return body

    def Parse8001(self, data):
        if len(data) < 5:
            return None
        resultTable = {0: "�ɹ�", 1: "ʧ��", 2: "��Ϣ����", 3: "��֧��", 4: "��������ȷ��"}
        body = dict()
        body["AckSeq"] = WORD2U16(data[:2])
        body["AckId"] = WORD2U16(data[2:4])
        body["Result"] = data[4]
        body["ResultText"] = resultTable.get(body["Result"], "*")
        return body

    def Parse0002(self, data):
        # �ն�����������Ϣ��Ϊ��
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
        resultTable = {0: "�ɹ�",
                       1: "�����ѱ�ע��",
                       2: "���ݿ����޸ó���",
                       3: "�ն��ѱ�ע��",
                       4: "���ݿ����޸��ն�"}
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
        # ��Ϣ ID�� 0x8107
        # ��ѯ�ն�������Ϣ��Ϊ��
        return None

    def Parse0107(self, data):
        body = dict()
        # 0 �ն����� WORD
        body['DevType'] = (data[0] << 8) | data[1]
        # 2 ������ ID BYTE[5] 5 ���ֽڣ��ն������̱��롣
        body['ManufacturerID'] = Hex2String(data[2:7])
        # 7 �ն��ͺ� BYTE[20] ���ն��ͺ������������ж��壬λ������ʱ���󲹡�0X00��
        body['Model'] = Byte2String(data[7:27])
        #body['Model'] = Hex2String(data[7:27])
        # 27 �ն� ID BYTE[7] �ɴ�д��ĸ��������ɣ����ն� ID �����������ж��壬λ������ʱ���󲹡�0X00����
        body['DevID'] = Byte2String(data[27:34])
        # 34 �ն� SIM �� ICCID BCD[10] �ն� SIM �� ICCID ��
        body['ICCID'] = BCD2String(data[34:44])
        # 44 �ն�Ӳ���汾�ų��� BYTE
        body['HWVerLen'] = n = data[44]
        # 45 �ն�Ӳ���汾�� STRING
        offset = 45
        body['HWVer'] = Byte2String(data[offset:offset+n])
        # 45+n �ն˹̼��汾�ų��� BYTE
        offset = offset + n
        body['SWVerLen'] = m = data[offset]
        # 45+n+1 �ն˹̼��汾�� STRING
        offset = offset + 1
        body['SWVer'] = Byte2String(data[offset:offset+m])
        # 45+n+1+m GNSS ģ������
        offset = offset + m
        body['AttrGNSS'] = data[offset]
        # 45+n+1+m+1 ͨ��ģ������
        offset = offset + 1
        body['AttrCOMM'] = data[offset]
        return body

    def Parse8108(self, data):
        body = dict()
        # 0 �������� BYTE
        body["Type"] = data[0]
        body["ManufacturerId"] = BCD2String(data[1:6])
        # 1 ������ ID BYTE[5] �����̱��

        # 6 �汾�ų��� BYTE n
        body["VernoLen"] = vernoLen = data[6]
        # 7 �汾�� STRING
        offset = 7 + vernoLen
        body["Verno"] = Byte2String(data[7:offset])
        # 7+n �������ݰ����� DWORD ��λΪ BYTE
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
        # ��չЭ��
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
                elif ext_id == 0x31:  # 0x31 ������
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
                    # �豸��б�Ƕ�
                    extData["DevAngle"] = data[idx + 1]
                elif ext_id == 0xE6:
                    # ��ѹ,�ٷ�֮һ��
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
                    extData["LBS"] = "��վ��λ"
                elif ext_id == 0xE2:
                    extData['Percent'] = int(WORD2U16(ext_body) / 100)
                elif ext_id == 0xE3:
                    extData["����ʱ��"] = "%02X/%02X/%02X %02X:%02X:%02X" % (ext_body[0],
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
        0 ������־ DWORD ������־λ����� �� 24
        4 ״̬ DWORD ״̬λ����� �� 25
        8 γ�� DWORD �Զ�Ϊ��λ��γ��ֵ����10��6�η�����ȷ�������֮һ��
        12 ���� DWORD �Զ�Ϊ��λ�ľ���ֵ����10��6�η�����ȷ�������֮һ��
        16 �߳� WORD ���θ߶ȣ���λΪ�ף�m��
        18 �ٶ� WORD 1/10km/h
        20 ���� WORD 0-359������Ϊ 0��˳ʱ��
        21 ʱ�� BCD[6] YY-MM-DD-hh-mm-ss��GMT+8 ʱ�䣬����׼��֮���漰��ʱ������ô�ʱ��
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
        # ת����bytes
        def ToBytearray(data):
            ba = bytearray()
            for i in range(0, len(data), 2):
                tmp = int(data[i:i+2], 16)
                ba.append(tmp)
            return ba
        # ��ת��

        def Unescape(data=b''):
            self.LOGD("data:" + str(data))
            length = data[2] << 8 | data[3]
            if 12 + length + 1 == len(data):
                self.LOGD("No escape")
            else:
                data = data.replace(b'\x7d\x02', b'\x7e')
                data = data.replace(b'\x7d\x01', b'\x7d')
            return data

        # ȥ�ո�
        buffer = data.replace(' ', '').upper()
        if buffer.startswith("7E"):
            buffer = buffer[2:]
        if buffer.endswith("7E"):
            buffer = buffer[:-2]
        if len(buffer) == 0 or len(buffer) / 2 == 1:
            self.LOGI("���Ȳ�ӦΪ0 �� ����")
            return None

        if buffer[0] != '0' and buffer[0] != '8':
            self.LOGI("msgid��0��8��ͷ")
            return None

        try:
            buffer = ToBytearray(buffer)
            buffer = Unescape(buffer)
        except Exception as e:
            self.LOGE("Reverse>>" + str(e) + '|' + str(data))
            buffer = None
        else:
            if self.lastData == buffer:
                self.LOGI("self.lastData == buffer")
                return None
            self.lastData = buffer
            buffer = buffer[:-1]  # ����У����

        if None == buffer:
            self.LOGI("None == buffer")
            return None

        offset = 0
        try:
            header = self.ParseHeader(buffer)
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
            #self.LOGW(u"δ�������Ϣ: %04X >> %s" % (msgId, data))
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
            return None

        retList = []
        for data in dataList:
            data = data.strip()
            try:
                retsult = self.ParseData(data)
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

        return "δ֪ID:" + msgId

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
            line = line.strip().upper()  # ͳһ��д

            if len(line) <= len("7e02007e"):
                continue

            if 'INFO - ����:' in line or 'INFO - ����:' in line or \
                    ("[����]" in line or "[����]" in line):
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

    # ��0200������ת����kml�õ�λ������
    def JT808ToLocation(self, msg=dict()):
        if msg['MsgId'] != 0x0200 or msg.get("Status") == None:
            return None
        status = int(msg["Status"][0], 16)
        if (status & 0x2) == 0:
            # δ��λ
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

    def PaserAndSave(self, logs, name, path=''):
        if len(logs) == 0:
            return
        result = self.ParseMultiLog(logs)
        print(result)

# �豸���Ӽ���
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