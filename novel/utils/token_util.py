# novel\utils\jwt_util.py
import os

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY',"dwalgntehsitbesgodwagvrtdsjzsedwachsejete")
ALGORITHM = "HS256"

# 过期时间配置
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 访问令牌 30 分钟有效
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 刷新令牌 7 天有效


class JwtUtil:
    """
    JWT 工具类
    负责生成和验证 Access Token 和 Refresh Token
    """

    @staticmethod
    def _create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
        """
        内部方法：生成 Token 的核心逻辑
        """
        to_encode = data.copy()

        # 设置过期时间 (exp)
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})

        # 设置签发时间 (iat)
        to_encode.update({"iat": datetime.now(timezone.utc)})

        # 生成 JWT
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """
        生成 Access Token
        通常包含 user_id, role 等少量信息，有效期短
        """
        return JwtUtil._create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        生成 Refresh Token
        通常只包含 user_id，有效期长，用于换取新的 Access Token
        """
        return JwtUtil._create_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证 Token 是否有效
        :return: 如果有效，返回 payload (字典)；如果无效或过期，返回 None
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # jwt.decode 会自动检查 exp (过期时间)，如果过期会抛异常
            return payload
        except jwt.ExpiredSignatureError:
            # Token 已过期
            return None
        except jwt.InvalidTokenError:
            # Token 无效（签名错误、格式错误等）
            return None

    @staticmethod
    def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        专门验证 Access Token
        可以在这里增加额外的检查，比如检查 token 类型标记
        """
        payload = JwtUtil.verify_token(token)
        if payload:
            # 可选：检查 payload 中是否包含特定标记，确保这是 Access Token 而不是 Refresh Token
            # if payload.get("type") != "access": return None
            return payload
        return None