import pytest
from pyairfocusexporter.models.workspace import WorkspaceData
from pyairfocusexporter.models.item import ItemData


def test_workspace_data_creation() -> None:
    workspace = WorkspaceData(id="ws-1", name="Test Workspace")
    assert workspace.id == "ws-1"
    assert workspace.name == "Test Workspace"
    assert workspace.items == []


def test_item_data_creation() -> None:
    item = ItemData(id="item-1", title="Test Item", type="task")
    assert item.id == "item-1"
    assert item.title == "Test Item"
    assert item.type == "task"


def test_workspace_with_items() -> None:
    item = ItemData(id="item-1", title="Test Item", type="task")
    workspace = WorkspaceData(id="ws-1", name="Test", items=[item])
    assert len(workspace.items) == 1
    assert workspace.items[0].title == "Test Item"
