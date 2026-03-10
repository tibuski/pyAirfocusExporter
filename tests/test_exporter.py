import pytest
from pyairfocusexporter.exporter.miro_exporter import MiroExporter
from pyairfocusexporter.models.workspace import WorkspaceData


def test_miro_exporter_validate_config() -> None:
    exporter = MiroExporter(access_token="", board_id="board-1")
    is_valid = exporter.validate_config()
    assert is_valid is False

    exporter_with_token = MiroExporter(access_token="token", board_id="board-1")
    is_valid = exporter_with_token.validate_config()
    assert is_valid is True


def test_miro_exporter_creation() -> None:
    exporter = MiroExporter(access_token="test-token", board_id="board-123")
    assert exporter.access_token == "test-token"
    assert exporter.board_id == "board-123"
