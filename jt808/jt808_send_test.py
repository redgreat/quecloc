# usr/bin/env python
# conding:utf-8

appid = "wx4d4xxxx"
screct = "522xxxx4"
template_id = 'IG1Kxxbxxxxxls'

class WechatMessagePush:
    def __init__(self, appid, appsecret, temple_id):
        self.appid = appid
        self.appsecret = appsecret

        # ģ��id,�ο����ںź����ģ����Ϣ�ӿ� -> ģ��ID(���ڽӿڵ���):IG1Kwxxxx
        self.temple_id = temple_id

        self.token = self.get_Wechat_access_token()


    def get_Wechat_access_token(self):
        '''
        ��ȡ΢�ŵ�access_token�� ��ȡ���ýӿ�ƾ֤
        :return:
        '''
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        response = requests.get(url)

        res = response.json()
        if "access_token" in res:
            token = res["access_token"]
            return token

    def get_wechat_accout_fans_count(self):
        '''
        ��ȡ΢�Ź��ں����з�˿��openid
        '''
        next_openid = ''
        url = f"https://api.weixin.qq.com/cgi-bin/user/get?access_token={self.token}&next_openid={next_openid}"
        response = requests.get(url)
        res = response.json()['data']['openid']

    def send_wechat_temple_msg(self, content):
        '''
        ����΢�Ź��ںŵ�ģ����Ϣ'''
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.token}"

        fan_open_id = self.get_wechat_accout_fans_count()
        for open_id in fan_open_id:
            body = {
                "touser": open_id,
                'template_id': self.temple_id,
                # 'url': 'http://www.jb51.net',
                "topcolor": "#667F00",
                "data": {
                    "content": {"value": content}
                }
            }
            headers = {"Content-type": "application/json"}
            data = json.JSONEncoder().encode(body)
            res = requests.post(url=url, data=data, headers=headers)
            WatchԤ����Ϣ