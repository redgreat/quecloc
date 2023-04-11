#usr/bin/env python
#conding:utf-8
# JT808设备协议解析

import re
import datetime
import binascii

def BCC_Check(data):
    data = data.replace(' ', '')
    n = int(len(data) / 2)
    xor = 0
    for r in range(n):
        xor ^= int(data[2 * r:2 * r + 2], 16)
    xor = hex(xor)

    if len(xor) != 4:
        xor = '0' + xor[2:]
    else:
        xor = xor[2:]
    return xor

def loca_report(rule,data):
    loca_data={}
    rule=rule+r'(?P<alarm_data>\w{8})(?P<status>\w{8})(?P<lat>\w{8})(?P<lng>\w{8})(?P<hight>\w{4})(?P<speed>\w{4})(?P<dirct>\w{4})(?P<dev_upload>\w{12})'
    attch_data=data[len(re.search(rule,data).group()):]
    data=re.search(rule,data).groupdict()

    alarm_data=data['alarm_data']
    alarm_happen=''
    for x in range(len(alarm_data)):
        alarm_happen+='{:04b}'.format(int(alarm_data[x],16))
        
    all_alarm=[]
    if alarm_happen[-1]=='1':
        all_alarm.append('sos_alarm')#紧急报警

    if alarm_happen[-2]=='1':
        all_alarm.append('speed_alarm')#超速

    if alarm_happen[-3]=='1':
        all_alarm.append('fatigue_drive')#疲劳驾驶

    if alarm_happen[-6]=='1':
        all_alarm.append('antenna_alarm')#天线故障

    if alarm_happen[-8]=='1':
        all_alarm.append('low_power')#低电压报警

    if alarm_happen[-9]=='1':
        all_alarm.append('power_cut')#断电报警

    if alarm_happen[-18]=='1':
        all_alarm.append('remove_alarm')#拆除报警

    if alarm_happen[-29]=='1':
        all_alarm.append('illegal_move_alarm')#非法位移报警

    status=data['status']
    status_happen=''
    for x in range(len(status)):
        status_happen+='{:04b}'.format(int(status[x],16))
    all_status=[]
    if status_happen[-1]=='1':
        all_status.append('acc_on')
    else:
        all_status.append('acc_off')

    if status_happen[-2]=='1':
        all_status.append('track')
    else:
        all_status.append('un_track')

    if status_happen[-11]=='0':
        all_status.append('oil_normal')
    else:
        all_status.append('oil_cut')

    if status_happen[-12]=='0':
        all_status.append('ele_normal')
    else:
        all_status.append('ele_cut')

    lat=int(data['lat'], 16) / pow(10, 6)
    lng=int(data['lng'], 16) / pow(10, 6)
    hight=str(int(data['hight'],16))
    speed=str(int((int(data['speed'],16)/10)))
    dirct=str(int(data['dirct'],16))
    dev_upload=data['dev_upload']
    dev_upload='20%s-%s-%s %s:%s:%s'%(dev_upload[0:2],dev_upload[2:4],dev_upload[4:6],dev_upload[6:8],dev_upload[8:10],dev_upload[10:12])

    if attch_data:
        def handle_atth(d):
            attch_rule=r'(?P<msg_id>\w{2})(?P<msg_len>\w{2})'
            msg_head=d[0:4]
            res=re.search(attch_rule,msg_head).groupdict()
            msg_id=res['msg_id']
            msg_len=int(res['msg_len'],16)*2
            value=d[4:4+msg_len]
            if msg_id=='01':
                value=int(value,16)/10
                loca_data['mileage']=value#里程
            elif msg_id=='02':
                value=int(value,16)/10
                loca_data['oil']=value#油耗
            elif msg_id=='03':
                value=int(value,16)/10
                loca_data['speed']=value#速度
            elif msg_id=='30':
                value=int(value,16)
                loca_data['rssi']=value#通讯信号强度
            elif msg_id=='31':
                value=int(value,16)
                loca_data['gnss_num']=value#定位卫星颗数
            else:
                return
            handle_len=4+msg_len
            next_data=d[handle_len:]
            if len(next_data)>0:
                handle_atth(next_data)
        handle_atth(attch_data)
    loca_data.update(lat=lat,lng=lng,alarm=str(all_alarm),status=str(all_status),hight=hight,speed=speed,dirct=dirct,dev_upload=dev_upload)
    return loca_data

def jt808_resopnes(responekind,mesg_head,mesg_result):
    response='0'
    auth='618669860425'
    mesg_id=mesg_head['mesg_id']
    phone_num=mesg_head['phone_num']
    mesg_num=mesg_head['mesg_num']

    if responekind=='8001':
        mesg_perp=  '%04x' % int(len(mesg_num+mesg_id)/2 + 1)
        response_body=responekind+mesg_perp+phone_num+'0000'+mesg_num+mesg_id+mesg_result
    elif responekind=='8100':
        mesg_perp=  '%04x' % int(len(mesg_num+auth)/2 + 1)
        response_body=responekind+mesg_perp+phone_num+'0000'+mesg_num+mesg_result+auth
    response_check=BCC_Check(response_body)
    response_body=response_body+response_check
    response_body=response_body.replace('7d','7d01')
    response='7e'+response_body.replace('7e','7d02')+'7e'
    response=binascii.a2b_hex(response)
    return response

def jt808_analysis(data,serv_receive,device_id='0'):

    response=b'0'
    all_data={}
    all_data['device_id']=device_id
    all_data['save_kind']='no'
    all_data['serv_receive']=serv_receive
    data=binascii.hexlify(data).decode()
    data=data[2:-2].replace('7d02','7e')
    data=data.replace('7d01','7d')
    # 校验
    if BCC_Check(data[0:-2]) == data[-2:]:
        pass
    else:
        all_data['response']=response
        return all_data
    # 去掉校验码，获取需要解析的数据字段
    data=data[0:-2]
    # 数据头处理，命令id，是否包含分包处理，电话号码，数据流水号
    rule=r'(?P<mesg_id>\w{4})(?P<mesg_explain>\w{4})(?P<phone_num>\w{12})(?P<mesg_num>\w{4})'
    head_len=len(re.search(rule,data).group())
    result=re.search(rule,data).groupdict()
    mesg_id=result['mesg_id']
    phone_num=result['phone_num']
    mesg_num=result['mesg_num']
    all_data['device_id']=str(int(phone_num))

    response=jt808_resopnes('8001',result,'00')
    mesg_explain=''
    for x in range(len(result['mesg_explain'])):
        mesg_explain+='{:04b}'.format(int(result['mesg_explain'][x],16))

    mesg_split=mesg_explain[2]
    mesg_encryption=mesg_explain[5]
    if mesg_split=='1':
        rule=rule+r'(?P<mesg_total_num>\w{4})'+r'(?P<mesg_order_num>\w{2})'
    if mesg_encryption=='1':
        #消息体RSA解密转码
        print('RSA_algorithm_encryption')

    if mesg_id=='0001':#终端回应平台下发指令
        rule=rule+r'(?P<answer_num>\w{4})(?P<answer_id>\w{4})(?P<command_result>\w{2})'
        data=re.search(rule,data).groupdict()
        # print('0001：终端回应平台下发指令',data)

    # 设备登录
    elif mesg_id=='0100':
        # if len(data)-head_len==76:
        rule=rule+r'(?P<Provincial_ID>\w{4})(?P<City_County_ID>\w{4})(?P<Manufacturer_ID>\w{10})(?P<Terminal_model>\w{16})(?P<Terminal_ID>\w{14})(?P<car_num_color>\w{2})(?P<car_identification>\w{2})'
        data=re.search(rule,data).groupdict()
        all_data.update(data)
        response=jt808_resopnes('8100',result,'00')
        all_data['save_kind']='yes'

    # 主要的位置上报信息
    elif mesg_id=='0200':
        loca_data=loca_report(rule,data)
        all_data.update(loca_data)
        all_data['save_kind']='yes'

    elif mesg_id=='0201':
        data_head=data[0:head_len]
        data_body=data[head_len:]
        handle_data=data_head+data_body[4:]
        loca_data=loca_report(rule,data)
        all_data.update(loca_data)
        all_data['save_kind']='yes'
        print('0201：终端查询位置信息回复')

    elif mesg_id=='0704':
        #print('0704：多条数据上传')
        rule=rule+r'(?P<data_num>\w{4})(?P<data_type>\w{2})(?P<detail>\w*)'
        res=re.search(rule,data).groupdict()
        data_num=int(res['data_num'],16)
        type_dict={'00':'正常','01':'补报'}
        data_type=type_dict[res['data_type']]
        detail=res['detail']
        multi_rule=rule=r'(?P<mesg_explain>\w{4})(?P<phone_num>\w{12})(?P<mesg_num>\w{4})'
        all_loca=[]
        for x in range(data_num):
            data_len=int(detail[0:4],16)*2
            handle_len=4+data_len
            data_body=detail[4:handle_len]
            data_res=loca_report('',data_body)
            detail=detail[handle_len:]
            lng=data_res.get('lng')

            if lng not in [0.0,'','0',None]:
                data_res['device_id']=all_data['device_id']
                data_res['serv_receive']=serv_receive
                all_loca.append(data_res)

        all_data['save_kind']='yes'
        all_data['all_loca']=all_loca
    all_data['response']=response
    return all_data
