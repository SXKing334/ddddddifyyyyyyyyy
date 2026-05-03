# novel/domain/entity/user.py

from dataclasses import dataclass
import bcrypt


@dataclass
class User:
    """
    用户领域实体
    负责处理与用户相关的核心业务逻辑，例如密码加密和验证。
    """
    username: str
    tenant_id: int
    password: str = ""  # 存储的是哈希值，不再是明文密码
    role: str = "user"
    id: int = None        # 如果是从数据库查出来的，会有ID

    @classmethod
    def create(cls, username: str, raw_password: str, tenant_id: int, role: str = "user") -> 'User':
        """
        工厂方法：用于创建一个新用户。
        这个方法会处理密码加密的逻辑。
        """
        if len(raw_password) < 6:
            raise ValueError("密码长度不能少于6位")

        # 核心：在这里进行密码加密
        password = cls._hash_password(raw_password)

        return cls(
            username=username,
            password=password,
            tenant_id=tenant_id,
            role=role
        )

    def verify_password(self, raw_password: str) -> bool:
        """
        验证用户输入的密码是否正确。
        """
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        私有方法：执行密码哈希。
        """
        # bcrypt.hashpw 会生成一个包含盐的哈希值
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')