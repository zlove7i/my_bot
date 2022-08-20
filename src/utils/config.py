from typing import Union
import os
import yaml
import socket

class Config():
    '''配置文件类'''

    def __new__(cls, *args, **kwargs):
        '''单例'''
        if not hasattr(cls, '_instance'):
            orig = super(Config, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    def __getattr__(self, item) -> dict[str, Union[str, int, bool]]:
        '''获取配置'''
        value = self._config.get(item)
        if value:
            return value
        raise AttributeError("未找到该配置字段，请检查config.yml文件！")

    def __init__(self):
        '''初始化'''
        root_path = os.path.realpath(__file__+"/../../../")
        config_file = os.path.join(root_path, "conf/config.yml")
        with open(config_file, 'r', encoding='utf-8') as f:
            cfg = f.read()
            self._config: dict = yaml.load(cfg, Loader=yaml.FullLoader)

        hostname = socket.gethostname()
        self._config['hostname'] = hostname
        main_host = self._config["node_info"].get("main_host")
        self._config['is_main_host'] = not main_host or main_host == hostname

        # data文件夹
        data: str = os.path.join(root_path, "data")
        datadir = os.path.join(root_path, data)
        if not os.path.isdir(datadir):
            os.makedirs(datadir)

        # log文件夹
        logs: str = os.path.join(root_path, "log")
        logsdir = os.path.join(root_path, logs)
        if not os.path.isdir(logsdir):
            os.makedirs(logsdir)


config = Config()
'''项目配置文件'''
