# pyAirfocusExporter

Export airfocus workspaces to external services like Miro.

## Setup

```bash
# Install dependencies
uv sync

# Copy and configure constants
cp pyairfocusexporter/constants.py.example pyairfocusexporter/constants.py
# Edit constants.py with your API keys
```

## Usage

```bash
# Show help
uv run pyairfocusexporter --help

# Export workspace (dry run)
uv run pyairfocusexporter export --workspace-id <ID> --dry-run

# Export to Miro
uv run pyairfocusexporter export --workspace-id <ID> --target miro --miro-board-id <BOARD_ID>
```

## Configuration

Edit `pyairfocusexporter/constants.py` with your API credentials:

- `AIRFOCUS_API_KEY`: Your airfocus API key
- `MIRO_ACCESS_TOKEN`: Your Miro access token
