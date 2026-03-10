from typing import Any, Optional
from pydantic import BaseModel, Field


class ExportError(BaseModel):
    message: str
    code: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class ExportResult(BaseModel):
    success: bool
    exported_count: int = 0
    error_count: int = 0
    errors: list[ExportError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration: float = 0.0
