from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


class WorkspaceData(BaseModel):
    id: str
    name: str
    description: Optional[Any] = None
    items: list["ItemData"] = Field(default_factory=list)
    child_workspaces: list["WorkspaceData"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def convert_description(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "description" in data and isinstance(data["description"], dict):
            desc = data["description"]
            if "blocks" in desc:
                data["description"] = cls._blocks_to_text(desc["blocks"])
            elif isinstance(desc.get("content"), str):
                data["description"] = desc["content"]
            else:
                data["description"] = str(desc)
        return data

    @staticmethod
    def _blocks_to_text(blocks: list[dict[str, Any]]) -> str:
        if not blocks:
            return ""
        texts = []
        for block in blocks:
            block_text = ""
            if "content" in block:
                for item in block["content"]:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            block_text += item.get("content", "")
                        elif item.get("type") in ("bold", "italic"):
                            block_text += item.get("content", "")
                    elif isinstance(item, str):
                        block_text += item
            texts.append(block_text)
        return "\n".join(texts)


from .item import ItemData
