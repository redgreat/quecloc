# usr/bin/env python
# conding:utf-8
# 微信公众号、企微推送预警消息

import requests
import json
from loguru import logger

wx_headers = {"Content-type": "application/json"}

#微信公众号
wx_appid = "wxb7df21e59521bdd2"
wx_secret = "2526ac4657a3d645a16c3e0774f70a80"
wx_temp_id = '9qERaOuoy_4Sa9BcqCoxg91jKm9t82ZDumGAy_6vpKo'

#企业微信
qw_key="ea50a2d0-2d51-4ba3-a90c-66919a51ca01"
qw_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={}'.format(qw_key)
qw_mentioned_list = []

alarm_dic = {
    "sos_alarm":"紧急报警",
    "speed_alarm":"超速报警",
    "fatigue_drive":"疲劳驾驶",
    "antenna_alarm":"天线故障",
    "low_power":"低电压报警",
    "power_cut":"断电报警",
    "remove_alarm":"拆除报警",
    "illegal_move_alarm":"非法位移报警",
}

class MsgHandler:
    def __init__(self):
        self.wx_headers = wx_headers
        self.wx_appid = wx_appid
        self.wx_secret = wx_secret
        self.wx_temp_id = wx_temp_id
        self.qw_key = qw_key
        self.qw_url = qw_url
        self.qw_mentioned_list = qw_mentioned_list
        self.alarm_dic = alarm_dic
        self.wx_token = self.get_wx_token()
        self.wx_account = self.get_wx_account()

    def get_wx_token(self):
        token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.wx_appid}&secret={self.wx_secret}"
        response = requests.get(token_url)
        res = response.json()
        if "access_token" in res:
            token = res["access_token"]
            return token

    def get_wx_account(self):
        next_openid = ''
        url = f"https://api.weixin.qq.com/cgi-bin/user/get?access_token={self.wx_token}&next_openid={next_openid}"
        response = requests.get(url)
        res = response.json()['data']['openid']
        return res

    def send_wx808_msg(self, content):
        try:
            wx_send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.wx_token}"
            for open_id in self.wx_account:
                body = {
                    "touser": open_id,
                    'template_id': wx_temp_id,
                    "topcolor": "#EF4A21",
                    "data": {
                        "msg": {"value": content}
                    }
                }
                data = json.JSONEncoder().encode(body)
                res = requests.post(url=wx_send_url, data=data, headers=self.wx_headers)
        except Exception as e:
            logger.error('Message Send Failed:{}',e)

    def send_multi_wx808_msg (self, summarytag, summarytime, content):
        try:
            wx_send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.wx_token}"
            content = content.lstrip('[').rstrip(']').replace('\'','').split(",")
            for content_send in content:
                content_send = content_send.lstrip(' ').rstrip(' ')
                content_send = alarm_dic.get(content_send, content_send)
                for open_id in self.wx_account:
                    body = {
                        "touser": open_id,
                        'template_id': wx_temp_id,
                        "topcolor": "#EF4A21",
                        "data": {
                            "device": {"value": summarytag,
                                       "color": "#0033FF"},
                            "eventtime": {"value": summarytime,
                                          "color": "#0033FF"},
                            "msg": {"value": content_send,
                                    "color": "#FF0033"}
                        }
                    }
                    res = requests.post(url=wx_send_url, json=body, headers=self.wx_headers)
        except Exception as e:
            logger.error('Multi Message Send Failed:{}',e)

    def send_qw_msg (self, content):
        try:
            data = {"msgtype": "text",
                    "text": {"content": content.decode(),
                             "mentioned_list": self.qw_mentioned_list
                             }
                    }
            requests.post(url=self.qw_url, json=data, headers=self.wx_headers)
        except Exception as e:
            logger.error('Message Send Failed:{}',e)