# novel/domain/entity/tenant.py
from dataclasses import dataclass
from typing import Optional
import hashlib
import hmac


@dataclass
class Tenant:
    """
    租户领域实体
    负责处理租户相关的核心业务逻辑，如 API 鉴权和配额检查。
    """
    name: str
    app_id: str
    plan: str
    quota_max_chats: int
    is_active: bool = True
    secret: str = ""           # 存储 Secret 的哈希值，不存明文
    id: Optional[int] = None
    created_at = None          # 可以在这里定义，或者只在 ORM 层使用

    @classmethod
    def create(cls, name: str, app_id: str, raw_secret: str, plan: str = "free", quota_max_chats: int = 100):
        """
        工厂方法：创建新租户
        """
        if not app_id or len(app_id) < 4:
            raise ValueError("AppID 长度不能少于4位")

        if not raw_secret or len(raw_secret) < 8:
            raise ValueError("Secret 长度不能少于8位")

        # 核心：Secret 不要存明文！建议用 SHA256 或 HMAC
        secret = cls._hash_secret(raw_secret)

        return cls(
            name=name,
            app_id=app_id,
            secret=secret,
            plan=plan,
            quota_max_chats=quota_max_chats,
            is_active=True
        )

    def verify_secret(self, raw_secret: str) -> bool:
        """
        校验 API Secret
        用于第三方系统调用接口时的签名验证
        """
        input_hash = self._hash_secret(raw_secret)
        # 使用常量时间比较防止时序攻击
        return hmac.compare_digest(self.secret, input_hash)

    def check_quota(self, current_usage: int) -> bool:
        """
        检查配额是否超限
        :param current_usage: 当前已使用的次数
        :return: True 表示可用，False 表示超限
        """
        if not self.is_active:
            raise Exception("租户已被禁用")

        return current_usage < self.quota_max_chats

    @staticmethod
    def _hash_secret(secret: str) -> str:
        """
        私有方法：哈希 Secret
        API Secret 通常不需要像密码那样加盐（Salt），因为它是随机生成的字符串
        但为了安全，我们依然进行哈希存储
        """
        # 实际生产中，建议加一个全局的 SALT 环境变量
        return hashlib.sha256(secret.encode('utf-8')).hexdigest()