# novel\domain\entity\workflow.py
import datetime
from dataclasses import dataclass


@dataclass
class workflow:

    id : int
    tenant_id: int
    name: str = ""
    flow_json: dict | None = None
    status: int = 0
    created_by: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None






