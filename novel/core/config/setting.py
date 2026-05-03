# novel/core/config/setting.py
from dotenv import load_dotenv

from novel.core.config.app_setting import mysql, redis

load_dotenv()

class Setting:

    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.setting_table = {
            # 数据库
            "mysql": mysql,
            "redis": redis,
            "neo4j": {},
            "kafka": {},
            "vector": {},
            # model
            "model": {},
            # agent
            "agent": {},

        }


    def get_setting(self, key) -> dict:
        if key in self.setting_table:
            return self.setting_table[key]
        return {}

setting = Setting()
