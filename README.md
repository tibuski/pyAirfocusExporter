# pyAirFocusExporter

Export airfocus workspaces to external services like Miro.

## Setup

```bash
# Install dependencies
uv sync

# Copy and configure constants
cp pyairfocusexporter/constants.py.example pyairfocusexporter/constants.py
# Edit constants.py with your API keys and workspace ID
```

## Usage

```bash
# Show help
uv run pyairfocusexporter --help

# Export workspace (dry run) - uses WORKSPACE_ID from constants.py
uv run pyairfocusexporter export --dry-run

# Export workspace with CLI argument
uv run pyairfocusexporter export --workspace-id <ID> --dry-run

# Export to Miro
uv run pyairfocusexporter export --miro-board-id <BOARD_ID>
```

## Configuration

Edit `pyairfocusexporter/constants.py` with your credentials:

- `AIRFOCUS_API_KEY`: Your airfocus API key
- `AIRFOCUS_WORKSPACE_ID`: Your airfocus workspace ID (or use --workspace-id flag)
- `MIRO_ACCESS_TOKEN`: Your Miro access token
