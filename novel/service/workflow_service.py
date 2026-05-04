from datetime import datetime

from fastapi.params import Depends
from sqlalchemy import select, func, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from novel.agent.graph.builder import DynamicGraphBuilder
from novel.infrastructure.db.models.workflow import WorkFlow as WorkFlowORM
from novel.infrastructure.redis.repo.tentant_repo import TenantRedisRepository, get_tenant_redis_repo
from novel.infrastructure.redis.repo.user_repo import UserRedisRepository, get_user_redis_repo
from novel.infrastructure.redis.repo.workflow_repo import WorkflowRedisRepo, get_workflow_redis_repo
from novel.service.file_service import FileService
from novel.shared.schemas.public import APIResponse
from novel.shared.schemas.workflow import (
    Workflow as WorkflowSchema,
    WorkflowStart as WorkflowStartSchema, WorkflowList
)
from novel.utils.orm_to_dict import orm_to_dict


class WorkFlowService:
    """
    工作流服务层
    """

    def __init__(
            self,
            user_repo: UserRedisRepository = Depends(get_user_redis_repo),           # user的redis仓库
            tenant_repo: TenantRedisRepository = Depends(get_tenant_redis_repo),     # tenant的redis仓库
            workflow_repo: WorkflowRedisRepo = Depends(get_workflow_redis_repo),     # workflow的redis仓库
            file_service: FileService = Depends(FileService),                        # FileService服务
    ):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
        self.workflow_repo = workflow_repo

    async def run_workflow(self,db: AsyncSession ,start: WorkflowStartSchema) -> APIResponse:
        """
        运行工作流
        :param start:
        :return:
        """


    async def create_workflow(self, db: AsyncSession, workflow: WorkflowSchema) -> APIResponse:
        """
        创建租户下的工作流
        :param workflow:
        :return:
        """

        # 1. 类型转换
        workflow_orm = WorkFlowORM(
            tenant_id=workflow.tenant_id,
            name=workflow.name,
            status=workflow.status if workflow.status else 0,
            created_by=workflow.created_by,
            created_at=workflow.created_at if workflow.created_at else datetime.utcnow(),
            updated_at=workflow.updated_at if workflow.updated_at else datetime.utcnow(),
        )

        # 2. 获取id
        db.add(workflow_orm)
        await db.flush()

        # 3. 类型转换
        workflow_dict = orm_to_dict(workflow_orm)
        workflow_schema: WorkflowSchema = WorkflowSchema.model_validate(workflow_dict)

        # 4. 返回
        return APIResponse.success(
            code=200,
            data=workflow_schema
        )

    async def update_workflow(self, db: AsyncSession,workflow: WorkflowSchema) -> APIResponse:
        """
        更新特定租户工作流
        :param db:
        :param workflow:
        :return:
        """
        # 1. 获取老工作流
        existing_stmt = select(WorkFlowORM).where(
            WorkFlowORM.id == workflow.id,
            WorkFlowORM.tenant_id == workflow.tenant_id
        )
        existing_result = await db.execute(existing_stmt)
        existing_workflow = existing_result.scalar_one_or_none()

        # 2. 判断有无
        if not existing_workflow:
            return APIResponse(
                code=404,
                message=f"工作流不存在 (id={workflow.name})",
                data=None
            )

        # 3. 更新字段
        now = datetime.utcnow()
        update_data = {
            "name": workflow.name,
            "flow_json": workflow.workflow_json,
            "status": workflow.status if workflow.status is not None else existing_workflow.status,
            "updated_at": now
        }

        # 4. 执行更新
        stmt = update(WorkFlowORM).where(
            WorkFlowORM.id == workflow.id,
            WorkFlowORM.tenant_id == workflow.tenant_id
        ).values(**update_data)
        await db.execute(stmt)

        # 5. 查询更新后的数据
        select_stmt = select(WorkFlowORM).where(WorkFlowORM.id == workflow.id)
        select_result = await db.execute(select_stmt)
        updated_workflow = select_result.scalar_one()

        # 6. 转换为Schema
        workflow_dict = orm_to_dict(updated_workflow)
        workflow_schema = WorkflowSchema.model_validate(workflow_dict)

        # 7. 存入redis
        try:
            await self.workflow_repo.set_workflow_info(workflow.tenant_id, workflow.id, workflow_dict)
        except Exception as e:
            print("工作流缓存到redis失败")


        # 8. 返回
        return APIResponse.success(
            code=200,
            data=workflow_schema
        )

    async def select_workflow(self, db: AsyncSession, workflow: WorkflowSchema) -> APIResponse:
        """
        查看特定租户工作流
        :param db:
        :param workflow:
        :return:
        """
        # 1. 先查redis
        workflow_dict = await self.workflow_repo.get_workflow_info(workflow.tenant_id, workflow.id)
        if workflow_dict:
            workflow_schema = WorkflowSchema.model_validate(workflow_dict)
            return APIResponse.success(
                code=200,
                data=workflow_schema
            )



        # 2. 查询工作流（包含完整信息，包括 flow_json）
        stmt = select(WorkFlowORM).where(
            WorkFlowORM.id == workflow.id,
            WorkFlowORM.tenant_id == workflow.tenant_id
        )
        result = await db.execute(stmt)
        workflow_orm = result.scalar_one_or_none()

        # 3. 验证是否存在
        if not workflow_orm:
            return APIResponse(
                code=404,
                message=f"工作流不存在 ({workflow.name})",
                data=None
            )

        # 4. 转换为Schema
        workflow_dict = orm_to_dict(workflow_orm)
        workflow_schema = WorkflowSchema.model_validate(workflow_dict)

        # 5. 存redis
        try:
            await self.workflow_repo.set_workflow_info(workflow.tenant_id, workflow.id, workflow_dict)
        except Exception as e:
            print("工作流缓存redis失败")

        # 6. 返回
        return APIResponse.success(
            code=200,
            data=workflow_schema
        )

    async def delete_workflow(self, db: AsyncSession , workflow: WorkflowSchema) -> APIResponse:
        """
        删除特定租户工作流
        :param db:
        :param workflow:
        :return:
        """
        # 1. 验证工作流是否存在
        existing_stmt = select(WorkFlowORM).where(
            WorkFlowORM.id == workflow.id,
            WorkFlowORM.tenant_id == workflow.tenant_id
        )
        existing_result = await db.execute(existing_stmt)
        existing_workflow = existing_result.scalar_one_or_none()

        if not existing_workflow:
            return APIResponse(
                code=404,
                message=f"工作流不存在 ({workflow.name})",
                data=None
            )

        # 2. 检查是否已是发布状态（可选：发布的工作流不允许删除）
        if existing_workflow.status == 1:
            return APIResponse(
                code=400,
                message="已发布的工作流不能删除，请先停用",
                data=None
            )

        # 3. 执行删除
        stmt = delete(WorkFlowORM).where(
            WorkFlowORM.id == workflow.id,
            WorkFlowORM.tenant_id == workflow.tenant_id
        )
        await db.execute(stmt)

        # 4. 返回
        return APIResponse.success(
            code=200,
            data=None
        )

    async def list_workflow(self, db: AsyncSession, user: dict, page: int, page_size: int = 20) -> APIResponse:
        """
        分页查询特定租户的工作流
        :param db: 数据库会话
        :param user: 用户信息
        :param page: 当前要查询的页
        :param page_size: 每一页的尺寸
        :return: APIResponse
        """

        # 1. 获取租户信息
        tenant_id = user['tenant_id']

        # 2. 计算偏移量
        offset = (page - 1) * page_size


        # 3. 查数据库(只查workflow_id, name)
        count_stmt = select(func.count()).select_from(WorkFlowORM).where(
            WorkFlowORM.tenant_id == tenant_id
        )
        total = await db.execute(count_stmt)
        total_count = total.scalar()

        # 4. 查询列表数据（排除 flow_json 大字段）
        stmt = select(
            WorkFlowORM.id,
            WorkFlowORM.tenant_id,
            WorkFlowORM.name,
            WorkFlowORM.status,
            WorkFlowORM.updated_at
        ).where(
            WorkFlowORM.tenant_id == tenant_id
        ).order_by(
            WorkFlowORM.id.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        workflows = result.mappings().all()  # 返回字典格式

        # 5. 验证有无
        if not workflows and total_count > 0:
            return APIResponse(
                code=400,
                message=f"页数超出范围，总共有 {(total_count + page_size - 1) // page_size} 页",
                data=None
            )

        # 6. 构造响应格式
        workflow_list: WorkflowList = WorkflowList(
            tenant_id=tenant_id,
            page=page,
            per_page=page_size,
        )
        for workflow in workflows:
            workflow_list.append(workflow)

        # 7. 返回
        return APIResponse.success(
            code=200,
            data=workflow_list
        )


