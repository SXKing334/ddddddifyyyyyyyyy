# novel\infrastructure\db\models\file.py
from sqlalchemy import Column, JSON, Integer, String, BigInteger, Text, DateTime, func

from novel import Base


class File(Base):
    """文件表"""
    __tablename__ = "file"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文件id")
    file_hash = Column(String(64), nullable=False, comment="文件哈希值")
    file_name = Column(String(64), nullable=False, comment="文件名")
    file_path = Column(String(255), nullable=False, comment="文件存储路径（磁盘，oss）")
    file_size = Column(BigInteger, nullable=False, comment="文件大小")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    metadata = Column(JSON, nullable=True, comment="文件元数据")
    parse_status = Column(String(20), nullable=False, comment="文件解析状态：pending, parsing, completed, failed")
    parsed_content = Column(Text, nullable=True, comment="解析后的文本内容")
    parse_error = Column(String(255), nullable=True, comment="解析失败的原因")
    status = Column(String(20), nullable=False, comment="文件冷热状态：active, deleted")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="文件上传时间")

    def __repr__(self):
        return f"<File(id={self.id}, name={self.file_name}, status={self.status})>"



class UserFile(Base):
    """用户-文件关联表"""
    __tablename__ = "user_file"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="关联表的主键id")
    tenant_id = Column(Integer, nullable=False, comment="租户id")
    file_id = Column(Integer, nullable=False, comment="文件id")
    user_id = Column(Integer, nullable=False, comment="租户内哪个用户上传的")
    ref_id = Column(Integer, nullable=True, comment="引用ID（如workflow_id, knowledge_id）")
    permission = Column(String(20), nullable=False, comment="权限: read, write, owner")
    type = Column(String(30), nullable=False, comment="WORKFLOW_FILE/KNOWLEDGE_BASE")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="什么时候上传的")
    expires_at = Column(DateTime, nullable=True, comment="文件过期时间")

    def __repr__(self):
        return f"<UserFile(id={self.id}, user_id={self.user_id}, file_id={self.file_id}, type={self.type})>"

