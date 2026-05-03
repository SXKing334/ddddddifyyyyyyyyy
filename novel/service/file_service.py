# novel\service\file_service.py
"""
独立的文件服务
可以被工作流、知识库、等多个模块复用
"""
from enum import Enum

from fastapi import UploadFile


import os
import uuid
import aiofiles
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from novel.infrastructure.db.models.file import File
from novel.shared.schemas.public import APIResponse


class FileType(Enum):
    WORKFLOW_FILE = 1                 # 工作流输入文件
    KNOWLEDGE_BASE = 2                # 知识库文件

class FileService:
    """
    通用文件服务
    上传文件，轮询文件上传状态
    """

    # 文件存储目录
    UPLOAD_DIR = "uploads"
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    def __init__(
            self,
            storage_backend: str = "oss"
    ):
        """
        :param storage_backend: 存储后端 local, oss, s3
        """
        self.storage_backend = storage_backend
        self._ensure_upload_dir()

    def _ensure_upload_dir(self):
        """确保上传目录存在"""
        if self.storage_backend == "local":
            os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    async def _save_to_storage(self, file: UploadFile, file_id: str) -> str:
        """
        保存文件到存储
        返回文件路径
        """
        if self.storage_backend == "local":
            # 本地存储
            file_ext = os.path.splitext(file.filename)[1]
            save_path = os.path.join(self.UPLOAD_DIR, f"{file_id}{file_ext}")

            # 流式写入，不占内存
            async with aiofiles.open(save_path, 'wb') as f:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    await f.write(chunk)

            return save_path

        elif self.storage_backend == "oss":
            # TODO: 实现 OSS 上传
            pass

        else:
            raise ValueError(f"不支持的存储后端: {self.storage_backend}")

    async def upload_file(
            self,
            db: AsyncSession,
            file: UploadFile,
            tenant_id: str,
            file_type: FileType,
            background_tasks: BackgroundTasks = None,
            auto_parse: bool = True
    ) -> APIResponse:
        """
        MQ异步上传文件
        - 原文件保存到 OSS
        - 记录到文件表 和 用户文件关联表 并返回解析状态
        - 进行异步调用工具解析多模态文件并进行 向量化/三元组/内容提取 存入ES/neo4j/redis/vec/db
        - 更新结果状态返回前端（仅返回状态即可）
        （等用户引用文件时，低代码平台的rag节点从redis里拿出、或者用自适应rag的检索方式检索）
        """
        # 1. 生成文件ID
        file_id = uuid.uuid4().hex

        # 2. 保存文件
        file_path = await self._save_to_storage(file, file_id)

        # 3. 创建文件记录
        file_record = File(
            id=file_id,  # 使用生成的ID
            tenant_id=tenant_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_type.value,
            file_size=0,  # 可以在保存后获取实际大小
            parse_status="pending" if auto_parse else "skipped",
            status="active"
        )
        db.add(file_record)
        await db.flush()

        # 4. 如果需要解析
        if auto_parse and file_type in [FileType.WORKFLOW_INPUT, FileType.KNOWLEDGE_BASE]:
            if background_tasks:
                # 异步解析
                background_tasks.add_task(
                    self._parse_file_async,
                    db,  # 注意：db 不能跨任务共享，需要重新获取
                    file_record.id,
                    file_path
                )
            else:
                # 同步解析
                parsed = await self._parse_file_sync(file_path)
                file_record.parsed_content = parsed
                file_record.parse_status = "completed"
                file_record.parsed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(file_record)

        return FileInfo(
            file_id=file_record.id,
            file_path=file_record.file_path,
            status=file_record.status,
            parse_status=file_record.parse_status,
            filename=file_record.filename,
            file_size=file_record.file_size
        )

    async def _parse_file_async(self, file_id: str, file_path: str):
        """
        异步解析文件（后台任务）
        注意：这个函数在后台任务中运行，需要自己创建数据库会话
        """
        from novel.infrastructure.db.session import async_session

        try:
            # 创建新的数据库会话
            async with async_session() as db:
                # 更新状态为解析中
                await db.execute(
                    update(File)
                    .where(File.id == file_id)
                    .values(parse_status="parsing", updated_at=datetime.utcnow())
                )
                await db.commit()

                # 解析文件
                parsed_content = await self._parse_file_sync(file_path)

                # 更新解析结果
                await db.execute(
                    update(File)
                    .where(File.id == file_id)
                    .values(
                        parsed_content=parsed_content,
                        parse_status="completed",
                        parsed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()

                # 触发文件解析完成事件
                await self._on_file_parsed(db, file_id, parsed_content)

        except Exception as e:
            # 解析失败
            async with async_session() as db:
                await db.execute(
                    update(File)
                    .where(File.id == file_id)
                    .values(
                        parse_status="failed",
                        parse_error=str(e),
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()

    async def _parse_file_sync(self, file_path: str) -> str:
        """
        同步解析文件
        实际解析逻辑可以调用专门的解析器
        """
        # 根据文件类型解析
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.txt':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()

        elif ext == '.pdf':
            # 调用 PDF 解析器
            return await self._parse_pdf(file_path)

        elif ext == '.docx':
            # 调用 Word 解析器
            return await self._parse_docx(file_path)

        else:
            # 默认当作文本处理
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return await f.read()

    async def _parse_pdf(self, file_path: str) -> str:
        """解析PDF（在线程池中运行）"""
        import asyncio
        from pypdf import PdfReader

        def sync_parse():
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_parse)

    async def _parse_docx(self, file_path: str) -> str:
        """解析Word文档"""
        import asyncio
        import docx

        def sync_parse():
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_parse)

    async def _on_file_parsed(self, db: AsyncSession, file_id: str, content: str):
        """
        文件解析完成后的回调
        可以通知工作流继续执行
        """
        # 查找等待这个文件的工作流执行记录
        from novel.infrastructure.db.models.workflow_execution import WorkflowExecution

        stmt = select(WorkflowExecution).where(
            WorkflowExecution.file_id == file_id,
            WorkflowExecution.status == "pending"
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        # 触发工作流继续执行
        for execution in executions:
            # 这里可以通过事件、消息队列或直接调用
            # 为避免循环导入，使用事件发布
            await self._publish_file_ready_event(file_id, execution.id, content)

    async def _publish_file_ready_event(self, file_id: str, execution_id: int, content: str):
        """
        发布文件解析完成事件
        """
        # 简单实现：直接调用（需要避免循环导入）
        # 或者使用 Redis Pub/Sub
        # 或者使用 BackgroundTasks
        pass

    async def get_file_content(self, db: AsyncSession, file_id: str) -> Optional[str]:
        """
        获取文件解析后的内容
        """
        stmt = select(File).where(File.id == file_id)
        result = await db.execute(stmt)
        file = result.scalar_one_or_none()

        if file and file.parse_status == "completed":
            return file.parsed_content
        return None

    async def get_file_status(self, db: AsyncSession, file_id: str) -> Dict[str, Any]:
        """
        获取文件状态
        """
        stmt = select(File).where(File.id == file_id)
        result = await db.execute(stmt)
        file = result.scalar_one_or_none()

        if not file:
            return {"error": "文件不存在"}

        return {
            "file_id": file.id,
            "filename": file.filename,
            "parse_status": file.parse_status,
            "parse_error": file.parse_error,
            "file_size": file.file_size,
            "created_at": file.created_at.isoformat() if file.created_at else None,
            "parsed_at": file.parsed_at.isoformat() if file.parsed_at else None
        }

    async def delete_file(self, db: AsyncSession, file_id: str, tenant_id: str) -> bool:
        """
        删除文件
        """
        stmt = select(File).where(
            File.id == file_id,
            File.tenant_id == tenant_id
        )
        result = await db.execute(stmt)
        file = result.scalar_one_or_none()

        if not file:
            return False

        # 删除物理文件
        if self.storage_backend == "local" and os.path.exists(file.file_path):
            os.remove(file.file_path)

        # 软删除
        await db.execute(
            update(File)
            .where(File.id == file_id)
            .values(status="deleted", updated_at=datetime.utcnow())
        )
        await db.commit()

        return True