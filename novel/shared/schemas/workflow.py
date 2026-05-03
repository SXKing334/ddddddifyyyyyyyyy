# novel\shared\schemas\workflow.py
from typing import TypeVar, Generic

from pydantic import BaseModel, ConfigDict, Field


class Workflow(BaseModel):

    id: int | None = Field(default=None)
    tenant_id: int
    name: str
    workflow_json: dict = Field(default_factory=dict)
    status: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)


class WorkflowList(BaseModel):
    tenant_id: int
    page: int
    per_page: int
    workflow_list: list = Field(default_factory=list)


T = TypeVar("T")
class WorkflowStart(BaseModel, Generic[T]):
    id: int = Field(description="工作流id")
    tenant_id: int = Field(description="租户id")
    input_data: T