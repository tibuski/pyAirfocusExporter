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

### Airfocus
- `AIRFOCUS_API_KEY`: Your airfocus API key
- `AIRFOCUS_WORKSPACE_ID`: Your airfocus workspace ID (or use --workspace-id flag)

### Miro

**Option 1: Using access token directly**
- `MIRO_ACCESS_TOKEN`: Your Miro access token

To get an access token:
1. Go to https://miro.com/app/developer
2. Create a Developer team (free)
3. Create a new app to get `client_id` and `client_secret`
4. Follow the OAuth flow to get an access token

**Option 2: Using OAuth credentials (for future implementation)**
- `MIRO_CLIENT_ID`: Your Miro app client ID
- `MIRO_CLIENT_SECRET`: Your Miro app client secret