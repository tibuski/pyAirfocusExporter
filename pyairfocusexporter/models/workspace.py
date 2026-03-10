from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkspaceData(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    items: list["ItemData"] = Field(default_factory=list)
    child_workspaces: list["WorkspaceData"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


from .item import ItemData
