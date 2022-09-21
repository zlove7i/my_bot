from email.utils import parseaddr, formataddr
from email.mime.text import MIMEText
from email.header import Header

from aiosmtplib import SMTP, SMTPException
from src.utils.config import config
from src.utils.log import logger
from src.utils.db import my_bot, management

import random


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


class MailClient(object):

    def __new__(cls, *args, **kwargs):
        '''单例'''
        if not hasattr(cls, '_instance'):
            orig = super(MailClient, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        '''初始化'''
        self.sender = config.mail['sender']
        self.default_host = config.mail["default_host"]
        self.default_pord = config.mail["default_pord"]
        self.default_passwd = config.mail["default_passwd"]
        self.mail_list = config.mail['mail_list']

    async def send_mail(self, receiver, mail_title: str,
                        mail_content: str) -> None:
        mail_data = random.choice(self.mail_list)
        mail = mail_data.get('mail')
        passwd = mail_data.get('passwd', self.default_passwd)
        pord = mail_data.get('pord', self.default_pord)
        host = mail_data.get('host', self.default_host)
        message = MIMEText(mail_content, 'html')
        if isinstance(receiver, int):
            cui_receiver = my_bot.user_info.find_one({
                "_id": receiver
            }).get("email")
            if cui_receiver:
                receiver = cui_receiver
            else:
                receiver = f"{receiver}@qq.com"
        message["Subject"] = mail_title
        message['From'] = _format_addr(f"{self.sender} <{mail}>")
        message['To'] = _format_addr(f'用户老爷 <{receiver}>')
        msg = f"{self.sender}[{mail}] -> {receiver}: {mail_content}"
        logger.info(msg)

        try:
            async with SMTP(hostname=host, port=pord, use_tls=True) as smtp:
                await smtp.login(mail, passwd)
                await smtp.send_message(message)
        except SMTPException as e:
            log = f"发送邮件失败，原因：{str(e)}"
            logger.error(log)
        except Exception as e:
            logger.error(f"发送邮件失败，可能是你的配置有问题：{str(e)}")

    async def bot_offline(self, robot_id: int):
        management.bot_info.update_one({"_id": robot_id},
                                       {"$set": {
                                           "online_status": False
                                       }}, True)


mail_client = MailClient()
'''发送邮件客户端'''
