from pydantic import BaseModel, ConfigDict


class User(BaseModel):

    id: int | None = None
    role: str
    tenant_id: int
    username: str

    model_config = ConfigDict(from_attributes=True)









