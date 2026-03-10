from typing import Any, Optional
from pydantic import BaseModel, Field


class ItemData(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: str
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: list[str] = Field(default_factory=list)
