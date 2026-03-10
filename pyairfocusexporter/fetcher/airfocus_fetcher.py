from typing import Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.workspace import WorkspaceData
from ..models.item import ItemData
from ..utils.rate_limiter import HeaderBasedRateLimiter


class AirfocusFetcher:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.airfocus.com/api/v0",
        rate_limiter: Optional[HeaderBasedRateLimiter] = None,
        ignore_ssl: bool = False,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter or HeaderBasedRateLimiter()
        self._client: Optional[httpx.Client] = None
        self._ignore_ssl = ignore_ssl

    def __enter__(self) -> "AirfocusFetcher":
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

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        self.rate_limiter.acquire()

        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        response = self._client.request(method, f"{self.base_url}{path}", **kwargs)
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        if reset:
            reset_float = float(reset)
        else:
            reset_float = None
        self.rate_limiter.update_from_headers(int(remaining) if remaining else None, reset_float)
        return response

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def fetch_workspace(
        self,
        workspace_id: str,
        depth: int = 0,
        max_depth: Optional[int] = None,
    ) -> WorkspaceData:
        if max_depth is not None and depth > max_depth:
            return WorkspaceData(id=workspace_id, name="", items=[])

        response = self._request("GET", f"/workspaces/{workspace_id}")
        response.raise_for_status()
        data = response.json()

        workspace = WorkspaceData(
            id=data.get("id", workspace_id),
            name=data.get("name", ""),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
        )

        items = data.get("_embedded", {}).get("items", [])
        for item_data in items:
            workspace.items.append(self._parse_item(item_data))

        if max_depth is None or depth < max_depth:
            child_workspaces = data.get("_embedded", {}).get("childWorkspaces", [])
            for child_data in child_workspaces:
                child_id = child_data.get("id")
                if child_id:
                    child_workspace = self.fetch_workspace(
                        child_id, depth=depth + 1, max_depth=max_depth
                    )
                    workspace.child_workspaces.append(child_workspace)

        return workspace

    def _parse_item(self, data: dict[str, Any]) -> ItemData:
        return ItemData(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description"),
            type=data.get("type", "item"),
            status=data.get("status"),
            priority=data.get("priority"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            parent_id=data.get("parentId"),
            children_ids=data.get("childrenIds", []),
        )
