import time
from typing import Any, Optional
import miro_api
from miro_api import models

from ..models.workspace import WorkspaceData
from ..models.item import ItemData
from ..models.export import ExportResult, ExportError
from .base_exporter import BaseExporter
from ..utils.logging import get_logger

logger = get_logger()


class MiroExporter(BaseExporter):
    def __init__(
        self,
        access_token: str,
        board_id: Optional[str] = None,
    ):
        self.access_token = access_token
        self.board_id = board_id
        self._api: Optional[miro_api.MiroApi] = None
        self.item_cache: dict[str, str] = {}

    def __enter__(self) -> "MiroExporter":
        self._api = miro_api.MiroApi(self.access_token)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

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

        if not self._api:
            return ExportResult(
                success=False,
                error_count=1,
                errors=[ExportError(message="API client not initialized")],
                duration=time.time() - start_time,
            )

        try:
            workspace_items = self._group_items_by_workspace(workspace_data)

            position_x = 0
            position_y = 0

            for ws_name, items in workspace_items:
                logger.info(f"Exporting workspace: {ws_name} ({len(items)} items)")
                self._create_sticky_note(ws_name, position_x, position_y)
                position_y += 250

                ws_position_x = position_x
                ws_position_y = position_y

                for item in items:
                    try:
                        miro_item_id = self._create_card(item, ws_position_x, ws_position_y)
                        self.item_cache[item.id] = miro_item_id
                        exported_count += 1
                        ws_position_x += 300
                        if ws_position_x > 3000:
                            ws_position_x = ws_position_x - 3000 + position_x
                            ws_position_y += 200
                    except Exception as e:
                        errors.append(ExportError(message=f"Card creation failed: {e}"))

                position_y = ws_position_y + 200
                position_x = max(position_x, ws_position_x + 300)

            all_items = self._flatten_items(workspace_data)
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

    def _group_items_by_workspace(
        self, workspace: WorkspaceData
    ) -> list[tuple[str, list[ItemData]]]:
        result = []

        if workspace.items:
            result.append((workspace.name, list(workspace.items)))

        for child in workspace.child_workspaces:
            result.extend(self._group_items_by_workspace(child))

        return result

    def _flatten_items(self, workspace: WorkspaceData) -> list[ItemData]:
        items = list(workspace.items)
        for child in workspace.child_workspaces:
            items.extend(self._flatten_items(child))
        return items

    def _create_sticky_note(self, text: str, x: float, y: float) -> str:
        sticky_note_data = models.StickyNoteData(
            content=text,
            shape="square",
        )
        sticky_note = models.StickyNoteCreateRequest(
            data=sticky_note_data,
            position=models.PositionChange(x=x, y=y),
        )
        result = self._api.create_sticky_note_item(self.board_id, sticky_note)
        logger.debug(f"Created sticky note: {text}")
        return result.id

    def _create_card(self, item: ItemData, x: float, y: float) -> str:
        card_data = models.CardData(
            title=item.title,
        )
        card = models.CardCreateRequest(
            data=card_data,
            position=models.PositionChange(x=x, y=y),
        )
        result = self._api.create_card_item(self.board_id, card)
        logger.debug(f"Created card: {item.title}")
        return result.id

    def _create_connector(self, start_id: str, end_id: str) -> None:
        connector_data = models.ConnectorCreationData(
            start_item=models.Reference(id=start_id),
            end_item=models.Reference(id=end_id),
        )
        self._api.create_connector(self.board_id, connector_data)
        logger.debug(f"Created connector: {start_id} -> {end_id}")

    def cleanup(self) -> None:
        self.item_cache.clear()
