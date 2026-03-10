from abc import ABC, abstractmethod

from ..models.workspace import WorkspaceData
from ..models.export import ExportResult


class BaseExporter(ABC):
    @abstractmethod
    def export(self, workspace_data: WorkspaceData) -> ExportResult:
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        pass

    def cleanup(self) -> None:
        pass
