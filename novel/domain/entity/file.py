# novel/domain/entity/file.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class FileParseStatus(str, Enum):
    """文件解析状态"""
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileStatus(str, Enum):
    """文件状态"""
    ACTIVE = "active"
    DELETED = "deleted"


class FilePermission(str, Enum):
    """文件权限"""
    READ = "read"
    WRITE = "write"
    OWNER = "owner"


class FileType(str, Enum):
    """文件类型"""
    WORKFLOW_FILE = "WORKFLOW_FILE"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"


@dataclass
class File:
    """
    文件实体（业务层）
    不包含数据库相关逻辑，只包含业务属性和方法
    """
    id: Optional[int]
    file_hash: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    parse_status: FileParseStatus
    status: FileStatus
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    parsed_content: Optional[str] = None
    parse_error: Optional[str] = None

    def __post_init__(self):
        """初始化后的验证"""
        if self.file_size < 0:
            raise ValueError("文件大小不能为负数")
        if not self.file_name:
            raise ValueError("文件名不能为空")
        if not self.file_hash:
            raise ValueError("文件哈希不能为空")

    def is_parsed(self) -> bool:
        """文件是否已解析完成"""
        return self.parse_status == FileParseStatus.COMPLETED

    def is_parsing(self) -> bool:
        """文件是否正在解析"""
        return self.parse_status == FileParseStatus.PARSING

    def is_failed(self) -> bool:
        """文件解析是否失败"""
        return self.parse_status == FileParseStatus.FAILED

    def is_active(self) -> bool:
        """文件是否可用"""
        return self.status == FileStatus.ACTIVE

    def is_deleted(self) -> bool:
        """文件是否已删除"""
        return self.status == FileStatus.DELETED

    def get_content_preview(self, length: int = 500) -> str:
        """获取内容预览"""
        if not self.parsed_content:
            return ""
        return self.parsed_content[:length] + ("..." if len(self.parsed_content) > length else "")

    def mark_as_parsing(self):
        """标记为解析中"""
        self.parse_status = FileParseStatus.PARSING

    def mark_as_parsed(self, content: str):
        """标记为解析完成"""
        self.parse_status = FileParseStatus.COMPLETED
        self.parsed_content = content
        self.parse_error = None

    def mark_as_failed(self, error: str):
        """标记为解析失败"""
        self.parse_status = FileParseStatus.FAILED
        self.parse_error = error

    def mark_as_deleted(self):
        """标记为已删除"""
        self.status = FileStatus.DELETED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "file_hash": self.file_hash,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "metadata": self.metadata,
            "parse_status": self.parse_status.value if self.parse_status else None,
            "parsed_content": self.parsed_content,
            "parse_error": self.parse_error,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_db_model(cls, db_model) -> "File":
        """从数据库模型创建实体"""
        return cls(
            id=db_model.id,
            file_hash=db_model.file_hash,
            file_name=db_model.file_name,
            file_path=db_model.file_path,
            file_size=db_model.file_size,
            mime_type=db_model.mime_type,
            metadata=db_model.metadata,
            parse_status=FileParseStatus(db_model.parse_status),
            parsed_content=db_model.parsed_content,
            parse_error=db_model.parse_error,
            status=FileStatus(db_model.status),
            created_at=db_model.created_at,
        )


@dataclass
class UserFile:
    """
    用户-文件关联实体（业务层）
    管理用户和文件的关系
    """
    id: Optional[int]
    tenant_id: int
    file_id: int
    user_id: int
    permission: FilePermission
    type: FileType
    created_at: datetime
    ref_id: Optional[int] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后的验证"""
        if self.tenant_id <= 0:
            raise ValueError("租户ID无效")
        if self.user_id <= 0:
            raise ValueError("用户ID无效")
        if self.file_id <= 0:
            raise ValueError("文件ID无效")

    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_owner(self) -> bool:
        """是否是文件所有者"""
        return self.permission == FilePermission.OWNER

    def can_read(self) -> bool:
        """是否可读"""
        return self.permission in [FilePermission.READ, FilePermission.WRITE, FilePermission.OWNER]

    def can_write(self) -> bool:
        """是否可写"""
        return self.permission in [FilePermission.WRITE, FilePermission.OWNER]

    def can_delete(self) -> bool:
        """是否可删除"""
        return self.permission == FilePermission.OWNER

    def is_workflow_file(self) -> bool:
        """是否是工作流文件"""
        return self.type == FileType.WORKFLOW_FILE

    def is_knowledge_base_file(self) -> bool:
        """是否是知识库文件"""
        return self.type == FileType.KNOWLEDGE_BASE

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "file_id": self.file_id,
            "user_id": self.user_id,
            "ref_id": self.ref_id,
            "permission": self.permission.value if self.permission else None,
            "type": self.type.value if self.type else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
            "can_read": self.can_read(),
            "can_write": self.can_write(),
        }

    @classmethod
    def from_db_model(cls, db_model) -> "UserFile":
        """从数据库模型创建实体"""
        return cls(
            id=db_model.id,
            tenant_id=db_model.tenant_id,
            file_id=db_model.file_id,
            user_id=db_model.user_id,
            ref_id=db_model.ref_id,
            permission=FilePermission(db_model.permission),
            type=FileType(db_model.type),
            created_at=db_model.created_at,
            expires_at=db_model.expires_at,
        )