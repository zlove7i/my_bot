from email.utils import formataddr
from email.mime.text import MIMEText
from email.header import Header

from aiosmtplib import SMTP, SMTPException
from src.utils.config import config
from src.utils.log import logger
from src.utils.db import db

import random


class MailClient(object):
    '''发送邮件class'''
    _host: str
    '''服务器地址'''
    _pord: int
    '''服务器端口'''
    _user: str
    '''用户名'''
    _pass: str
    '''授权码'''
    _sender: str
    '''发送者'''
    _receiver: str
    '''接受方'''

    def __new__(cls, *args, **kwargs):
        '''单例'''
        if not hasattr(cls, '_instance'):
            orig = super(MailClient, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        '''初始化'''
        self.sender = config.mail['sender']
        self.mail_list = config.mail['mail_list']

    async def send_mail(self, receivers: list, mail_title: str,
                        mail_content: str) -> None:
        mail_data = random.choice(self.mail_list)
        mail = mail_data.get('mail')
        user = mail_data.get('user')
        passwd = mail_data.get('passwd')
        pord = mail_data.get('pord')
        host = mail_data.get('host')
        message = MIMEText(mail_content)
        receiver_list = []
        for receiver in receivers:
            if isinstance(receiver, int):
                cui_receiver = db.user_info.find_one({"_id": receiver}).get("email")
                if cui_receiver:
                    receiver = cui_receiver
                else:
                    receiver = f"{receiver}@qq.com"
            receiver_list.append(receiver)
        message["Subject"] = mail_title
        message['From'] = formataddr((Header(self.sender, 'utf-8').encode(), mail))
        msg = f"{self.sender}[{mail}] -> {receiver_list}: {mail_content}"
        logger.info(msg)

        try:
            async with SMTP(hostname=host, port=pord, use_tls=True) as smtp:
                await smtp.login(user, passwd)
                await smtp.send_message(message, mail, receiver_list)
        except SMTPException as e:
            log = f"发送邮件失败，原因：{str(e)}"
            logger.error(log)
        except Exception as e:
            logger.error(f"<r>发送邮件失败，可能是你的配置有问题：{str(e)}</r>")

    async def bot_offline(self, robot_id: int):
        db.bot_info.update_one({"_id": robot_id},
                               {"$set": {
                                   "online_status": False
                               }}, True)

mail_client = MailClient()
'''发送邮件客户端'''
