# novel\config\app_setting.py
import os

from dotenv import load_dotenv
from pydantic import BaseModel

from novel.exception.exceptions import MySQLLoadError, RedisLoadError

load_dotenv()

# ================ 数据库 ===================
# SQL
try:
    mysql = {
        'host': os.getenv('MYSQL_HOST'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'db': os.getenv('MYSQL_DBNAME'),
        'autocommit': True if os.getenv('AUTOCOMMIT') == 'True' else  False,
        'minsize': int(os.getenv('MYSQL_MINSIZE')),
        'maxsize': int(os.getenv('MYSQL_MAXSIZE'))
    }
except MySQLLoadError as e:
    print(f"数据库load_dotenv错误：{e}")
    raise MySQLLoadError("数据库load_dotenv错误")

# Redis
try:
    redis = {
        'host': os.getenv('REDIS_HOST'),
        'port': os.getenv('REDIS_PORT'),
        'db': os.getenv('REDIS_DB'),
        'password': os.getenv('REDIS_PASSWORD'),
        'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS')),
        'decode_responses': True if os.getenv('REDIS_DECODE_RESPONSES') == 'True' else False,
    }
except RedisLoadError as e:
    print(f"Redis load_dotenv错误：{e}")
    raise RedisLoadError("Redis load_dotenv错误")

# Redis

# Neo4j

# Vector

# ================== MQ ====================

# Kafka

