# Technical Specifications: pyAirfocusExporter
 
## 1. Project Overview
`pyAirfocusExporter` is a modular Python tool designed to extract data from airfocus workspaces and export them to various external services. The architecture must be decoupled to allow adding new export destinations (e.g., Miro, Notion, Trello) without modifying the core extraction logic. It must extract the root workspace information but also all the linked items from child workspaces. It must be clear for the user that he has to provide to top level workspace.
 
## 2. Technical Stack
- **Language:** Python 3.12+
- **Dependency Management:** `uv`
- **Libraries:** `httpx` (async HTTP client), `pydantic` (data validation), `click` or `argparse` (CLI), for `miro` use their python library https://developers.miro.com/docs/miro-python-client
 
## 3. CLI Interface
The script must support the following command-line arguments:
- `--workspace-id`: The ID of the airfocus workspace to extract.
- `--target`: The destination service (initially only `miro` is supported).
- `--dry-run`: (Optional) Fetch data without pushing to the target service.
 
## 4. Architecture: The Fetcher (airfocus API v0.*)
The core logic must handle airfocus-specific constraints:
- **Rate Limiting:** Respect the default limit of **600 requests/minute**. Monitor `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers [1, 2].
- **Data Enrichment:** Retrieve items and hierarchical relationships via the `_embedded` field [3].
- **Formatting:** Use the header `Accept: application/vnd.airfocus.markdown+json` to retrieve descriptions in Markdown format [4, 5].
- **Robustness:** Log the `X-Request-Id` for every response to facilitate bug reporting to airfocus [3].
- **Evolution:** Be prepared for breaking changes as the API is in `v0.*`. Use the JSON schema from `https://developer.airfocus.com/openapi.json` for stable code generation [1, 6, 7].
 
## 5. Architecture: The Exporter (Miro v2)
When `--target miro` is selected:
- **Board Items:** Create a Miro Card for each airfocus item [8].
- **Connectors:** Create Miro Connectors to represent parent/child links.
    - **Crucial:** The `startItem` and `endItem` fields are **mandatory** for connectors [9].
    - **Style:** Map link types to Miro connector shapes (straight, elbowed, or curved) [10].
- **Pagination:** Implement cursor-based pagination for large boards [11].
 
## 6. Configuration & Security
- **`constants.py`**: Must contain `AIRFOCUS_API_KEY`, `MIRO_ACCESS_TOKEN`, and other target-specific keys.
- **Git:** This file is excluded from version control.
- **Template:** Maintain `constants.py.example` with clear documentation for each constant.
 
## 7. Future Proofing
- Implement an abstract base class `BaseExporter` that any new service (Notion, Trello, etc.) must inherit from.
- The `Fetcher` should return a standardized internal Data Model (via Pydantic) that Exporters then translate into service-specific payloads.