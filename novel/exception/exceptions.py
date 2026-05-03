# novel\exception\exceptions.py

# SQLAlchemy
class SQLAlchemyEngineException(Exception):
    """数据库引擎错误"""
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message
class SQLAlchemySessionLocalException(SQLAlchemyEngineException):
    """数据库创建会话报错"""
    pass
# Redis
class RedisConnectionException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class MySQLLoadError(Exception):
    """
    自定义异常类，用于处理MySQL加载错误。
    """
    def __init__(self, message):
        super().__init__(message)
    pass
class RedisLoadError(Exception):
    """
    自定义异常类，用于处理Redis加载错误。
    """
    def __init__(self, message):
        super().__init__(message)
    pass