from pydantic import BaseModel, ConfigDict


class Tenant(BaseModel):
    id: int | None = None
    name: str
    plan: str

    model_config = ConfigDict(from_attributes=True)