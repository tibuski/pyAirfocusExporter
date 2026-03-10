from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


class ItemData(BaseModel):
    id: str
    title: str
    description: Optional[Any] = None
    type: str
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def convert_description(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "description" in data and isinstance(data["description"], dict):
            desc = data["description"]
            if "content" in desc and isinstance(desc["content"], str):
                data["description"] = desc["content"]
            elif "markdown" in desc:
                data["description"] = desc["markdown"]
            else:
                data["description"] = str(desc)
        return data
