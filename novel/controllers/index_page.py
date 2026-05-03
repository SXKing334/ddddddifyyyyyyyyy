from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio.session import AsyncSession

from novel.core.deps import get_current_user, require_permission
from novel.infrastructure.db.session import get_db_session
from novel.service.workflow_service import WorkFlowService
from novel.shared.schemas.public import APIResponse
from novel.shared.schemas.workflow import Workflow as WorkflowSchema

index_router = APIRouter(prefix="api/index",tags=["用户对话界面"])

@require_permission('flow:list')
@index_router.get("/list")
async def list(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20),
        user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session),
        workflow_service: WorkFlowService = Depends(WorkFlowService)
)-> APIResponse:

    result: APIResponse = await workflow_service.list_workflow(db, user, page, page_size)

    await db.commit()

    return result


@require_permission('flow:create')
@index_router.post("/create")
async def create(
        workflow: WorkflowSchema,
        db: AsyncSession = Depends(get_db_session),
        workflow_service: WorkFlowService = Depends(WorkFlowService)
) -> APIResponse:

    result: APIResponse = await workflow_service.create_workflow(db, workflow)

    await db.commit()

    return result

@require_permission('flow:edit')
@index_router.get("/edit")
async def edit(
        workflow: WorkflowSchema,
        db: AsyncSession = Depends(get_db_session),
        workflow_service: WorkFlowService = Depends(WorkFlowService)
)-> APIResponse:

    result: APIResponse = await workflow_service.update_workflow(db, workflow)

    await db.commit()

    return result


@require_permission('flow:delete')
@index_router.delete("/delete")
async def delete(
        workflow: WorkflowSchema,
        db: AsyncSession = Depends(get_db_session),
        workflow_service: WorkFlowService = Depends(WorkFlowService)
) -> APIResponse:

    result: APIResponse = await workflow_service.delete_workflow(db, workflow)

    await db.commit()

    return result


@require_permission('flow:publish')
@index_router.post("/publish")
async def publish(
        workflow: WorkflowSchema,
        db: AsyncSession = Depends(get_db_session),
        workflow_service: WorkFlowService = Depends(WorkFlowService)
) -> APIResponse:
    pass









