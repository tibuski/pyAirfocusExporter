from ..exporter.base_exporter import BaseExporter
from ..exporter.miro_exporter import MiroExporter


def get_exporter(
    target: str,
    access_token: str,
    board_id: str | None = None,
    ignore_ssl: bool = False,
) -> BaseExporter:
    if target.lower() == "miro":
        return MiroExporter(
            access_token=access_token,
            board_id=board_id,
            ignore_ssl=ignore_ssl,
        )
    raise ValueError(f"Unknown target: {target}")
