from typing import Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.workspace import WorkspaceData
from ..models.item import ItemData
from ..utils.rate_limiter import HeaderBasedRateLimiter
from ..utils.logging import get_logger

logger = get_logger()


class AirfocusFetcher:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.airfocus.com",
        rate_limiter: Optional[HeaderBasedRateLimiter] = None,
        ignore_ssl: bool = False,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter or HeaderBasedRateLimiter()
        self._client: Optional[httpx.Client] = None
        self._ignore_ssl = ignore_ssl

    def __enter__(self) -> "AirfocusFetcher":
        logger.debug("Initializing AirfocusFetcher")
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.airfocus.markdown+json",
            },
            verify=not self._ignore_ssl,
            timeout=30.0,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            self._client.close()
        logger.debug("AirfocusFetcher closed")

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        self.rate_limiter.acquire()

        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        logger.debug(f"Request: {method} {self.base_url}{path}")
        response = self._client.request(method, f"{self.base_url}{path}", **kwargs)

        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        if reset:
            reset_float = float(reset)
        else:
            reset_float = None
        self.rate_limiter.update_from_headers(int(remaining) if remaining else None, reset_float)

        logger.debug(f"Response status: {response.status_code}")
        return response

    def _fetch_items(self, workspace_id: str) -> list[dict[str, Any]]:
        items = []
        offset = 0
        limit = 1000

        while True:
            response = self._request(
                "POST",
                f"/api/workspaces/{workspace_id}/items/search",
                params={"offset": offset, "limit": limit},
                json={},
            )
            response.raise_for_status()
            data = response.json()

            items_page = data.get("items", [])
            count = len(items_page)
            logger.info(f"Fetched {count} items from workspace {workspace_id}")

            for item_data in items_page:
                item_id = item_data.get("id", "unknown")
                item_name = item_data.get("name", "Untitled")
                item_type = item_data.get("typeId", "unknown")
                parent_id = item_data.get("parentId")
                logger.debug(
                    f"  Item: {item_name} (id={item_id}, type={item_type}, parent={parent_id})"
                )

            items.extend(items_page)

            if len(items_page) < limit:
                break
            offset += limit

        logger.info(f"Total items fetched: {len(items)}")
        return items

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def fetch_workspace(
        self,
        workspace_id: str,
        depth: int = 0,
        max_depth: Optional[int] = None,
    ) -> WorkspaceData:
        if max_depth is not None and depth > max_depth:
            return WorkspaceData(id=workspace_id, name="", items=[])

        logger.info(f"Fetching workspace: {workspace_id} (depth: {depth})")
        response = self._request("GET", f"/api/workspaces/{workspace_id}")
        response.raise_for_status()
        data = response.json()

        workspace = WorkspaceData(
            id=data.get("id", workspace_id),
            name=data.get("name", ""),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
        )

        logger.info(f"Workspace name: {workspace.name}")

        items_data = self._fetch_items(workspace_id)
        for item_data in items_data:
            workspace.items.append(self._parse_item(item_data))

        if max_depth is None or depth < max_depth:
            child_workspaces = data.get("_embedded", {}).get("children", [])
            logger.info(f"Found {len(child_workspaces)} child workspaces")
            for child_data in child_workspaces:
                child_id = child_data.get("workspaceId")
                if not child_id and child_data.get("workspace"):
                    child_id = child_data["workspace"].get("id")
                if child_id:
                    logger.debug(f"Fetching child workspace: {child_id}")
                    child_workspace = self.fetch_workspace(
                        child_id, depth=depth + 1, max_depth=max_depth
                    )
                    workspace.child_workspaces.append(child_workspace)

        return workspace

    def _parse_item(self, data: dict[str, Any]) -> ItemData:
        return ItemData(
            id=data.get("id", ""),
            title=data.get("name", ""),
            description=data.get("description"),
            type=data.get("typeId", "item"),
            status=data.get("status"),
            priority=data.get("priority"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            parent_id=data.get("parentId"),
            children_ids=data.get("childrenIds", []),
        )
