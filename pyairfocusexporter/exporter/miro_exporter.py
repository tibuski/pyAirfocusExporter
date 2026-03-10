import time
from typing import Any, Optional
import httpx

from ..models.workspace import WorkspaceData
from ..models.item import ItemData
from ..models.export import ExportResult, ExportError
from .base_exporter import BaseExporter
from ..utils.rate_limiter import HeaderBasedRateLimiter


class MiroExporter(BaseExporter):
    def __init__(
        self,
        access_token: str,
        board_id: Optional[str] = None,
        base_url: str = "https://api.miro.com/v2",
        ignore_ssl: bool = False,
    ):
        self.access_token = access_token
        self.board_id = board_id
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.Client] = None
        self._ignore_ssl = ignore_ssl
        self.item_cache: dict[str, str] = {}
        self.rate_limiter = HeaderBasedRateLimiter(requests_per_minute=100, window_seconds=60)

    def __enter__(self) -> "MiroExporter":
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            verify=not self._ignore_ssl,
            timeout=30.0,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            self._client.close()

    def validate_config(self) -> bool:
        if not self.access_token:
            return False
        if not self.board_id:
            return False
        return True

    def export(self, workspace_data: WorkspaceData) -> ExportResult:
        start_time = time.time()
        errors: list[ExportError] = []
        warnings: list[str] = []
        exported_count = 0

        if not self.validate_config():
            return ExportResult(
                success=False,
                error_count=1,
                errors=[ExportError(message="Invalid configuration")],
                duration=time.time() - start_time,
            )

        try:
            all_items = self._flatten_items(workspace_data)
            position_x = 0
            position_y = 0

            for item in all_items:
                try:
                    miro_item_id = self._create_card(item, position_x, position_y)
                    self.item_cache[item.id] = miro_item_id
                    exported_count += 1
                    position_x += 300
                    if position_x > 3000:
                        position_x = 0
                        position_y += 200
                except Exception as e:
                    errors.append(ExportError(message=str(e)))

            for item in all_items:
                if item.parent_id and item.parent_id in self.item_cache:
                    parent_miro_id = self.item_cache.get(item.parent_id)
                    child_miro_id = self.item_cache.get(item.id)
                    if parent_miro_id and child_miro_id:
                        try:
                            self._create_connector(parent_miro_id, child_miro_id)
                        except Exception as e:
                            warnings.append(f"Connector failed: {e}")

        except Exception as e:
            errors.append(ExportError(message=str(e)))

        return ExportResult(
            success=len(errors) == 0,
            exported_count=exported_count,
            error_count=len(errors),
            errors=errors,
            warnings=warnings,
            duration=time.time() - start_time,
        )

    def _flatten_items(self, workspace: WorkspaceData) -> list[ItemData]:
        items = list(workspace.items)
        for child in workspace.child_workspaces:
            items.extend(self._flatten_items(child))
        return items

    def _create_card(self, item: ItemData, x: float, y: float) -> str:
        self.rate_limiter.acquire()

        if not self._client:
            raise RuntimeError("Client not initialized")

        response = self._client.post(
            f"{self.base_url}/boards/{self.board_id}/cards",
            json={
                "data": {
                    "title": item.title,
                    "description": item.description or "",
                },
                "position": {"x": x, "y": y},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("id", "")

    def _create_connector(self, start_id: str, end_id: str) -> None:
        self.rate_limiter.acquire()

        if not self._client:
            raise RuntimeError("Client not initialized")

        response = self._client.post(
            f"{self.base_url}/boards/{self.board_id}/connectors",
            json={
                "startItem": {"id": start_id},
                "endItem": {"id": end_id},
            },
        )
        response.raise_for_status()

    def cleanup(self) -> None:
        self.item_cache.clear()
