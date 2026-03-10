# Technical Specifications: pyAirfocusExporter

## 1. Project Overview
`pyAirfocusExporter` is a modular Python tool designed to extract data from airfocus workspaces and export them to various external services. The architecture is decoupled to allow adding new export destinations (e.g., Miro, Notion, Trello) without modifying the core extraction logic. The tool extracts root workspace information and recursively traverses all child workspaces. Users must provide the top-level workspace ID.

## 2. Technical Stack
- **Language:** Python 3.12+
- **Dependency Management:** `uv` (Python-only setup, no Docker)
- **Core Libraries:**
  - `httpx` (synchronous HTTP client)
  - `pydantic` (data validation and serialization)
  - `click` (CLI framework with automatic help display)
  - `rich` (colored output, progress bars, and formatting)
  - `tenacity` (retry logic with exponential backoff)
- **Development:**
  - `pytest` (minimal testing strategy, ~70% coverage)
  - `black`, `ruff` (code formatting and linting)
  - `mypy` (type checking)

## 3. CLI Interface Design
The CLI uses Click for intuitive command-line interface with automatic help display:

```bash
pyairfocusexporter export \
  --workspace-id <ID> \
  --target miro \
  --miro-board-id <BOARD_ID> \
  [--dry-run] \
  [--ignore-ssl] \
  [--stop-on-error] \
  [--max-depth <N>]
```

### Command-line Arguments:
- `--workspace-id` (required): The ID of the airfocus workspace to extract
- `--target` (required): Destination service (initially only `miro` is supported)
- `--miro-board-id` (required for miro): Miro board ID to export to
- `--dry-run`: Fetch data without pushing to the target service
- `--ignore-ssl`: Ignore SSL certificate verification (for development/testing)
- `--stop-on-error`: Halt execution on first error encountered
- `--max-depth`: Maximum recursion depth for child workspaces (default: unlimited)

### CLI Features:
- Automatic help display with `--help`
- Colored output using Rich library
- Progress bars for large exports
- Verbose logging with `--verbose` flag
- Clean error messages with suggestions

## 4. Configuration Management
### Constants Management:
- **`constants.py`**: Contains `AIRFOCUS_API_KEY`, `MIRO_ACCESS_TOKEN`, and other target-specific keys
- **Git Integration**: `constants.py` is excluded from version control via `.gitignore`
- **Template**: `constants.py.example` with clear documentation for each constant (NOT `.env` files)
- **Configuration Loading**: Priority order:
  1. Command-line arguments
  2. Environment variables
  3. `constants.py` file
  4. Default values

### Example `constants.py.example`:
```python
# Airfocus API Configuration
AIRFOCUS_API_KEY = "your_airfocus_api_key_here"
AIRFOCUS_API_BASE_URL = "https://app.airfocus.com"

# Miro Configuration
MIRO_ACCESS_TOKEN = "your_miro_access_token_here"
MIRO_API_BASE_URL = "https://api.miro.com/v2"

# Rate Limiting Configuration
AIRFOCUS_RATE_LIMIT_REQUESTS = 600  # requests per minute
AIRFOCUS_RATE_LIMIT_WINDOW = 60     # seconds
MIRO_RATE_LIMIT_REQUESTS = 100      # requests per minute
MIRO_RATE_LIMIT_WINDOW = 60         # seconds

# Request Configuration
REQUEST_TIMEOUT = 30.0              # seconds
MAX_RETRIES = 3                     # maximum retry attempts
RETRY_DELAY = 1.0                   # initial retry delay in seconds
```

## 5. Architecture: The Fetcher

### Core Features:
- **Synchronous Architecture**: Simple and straightforward implementation
- **Recursive Child Workspace Traversal**: Extract all levels of child workspaces
- **Rate Limiting**: Respect airfocus limit of **600 requests/minute** with token bucket algorithm
- **Request Tracking**: Log `X-Request-Id` for every response to facilitate bug reporting
- **Data Enrichment**: Retrieve items and hierarchical relationships via `_embedded` field
- **Markdown Formatting**: Use `Accept: application/vnd.airfocus.markdown+json` header
- **Stop-on-Error Behavior**: Configurable error handling with graceful degradation

### Implementation Details:
```python
class AirfocusFetcher:
    def __init__(self, api_key: str, base_url: str, rate_limiter: RateLimiter):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = rate_limiter
    
    def fetch_workspace(self, workspace_id: str, depth: int = None) -> WorkspaceData:
        """Recursively fetch workspace and all child workspaces"""
        pass
    
    def fetch_child_workspaces(self, parent_id: str, current_depth: int, max_depth: int) -> List[WorkspaceData]:
        """Recursively fetch child workspaces up to max_depth"""
        pass
```

### Rate Limiting Strategy:
- Token bucket algorithm with 600 tokens/minute
- Monitor `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- Automatic backoff when approaching limits

## 6. Architecture: The Exporter (Miro v2)

### Core Features:
- **Miro v2 API Integration**: Use httpx with proper authentication
- **Board Items**: Create Miro Cards for each airfocus item with proper formatting
- **Connectors**: Create Miro Connectors to represent parent/child links with `startItem` and `endItem` fields
- **Style Mapping**: Map airfocus link types to Miro connector shapes (straight, elbowed, curved)
- **Pagination**: Implement cursor-based pagination for large boards
- **Batch Operations**: Group operations for performance optimization

### Implementation Details:
```python
class MiroExporter(BaseExporter):
    def __init__(self, access_token: str, board_id: str = None):
        self.client = MiroClient(access_token=access_token)
        self.board_id = board_id
        self.item_cache = {}  # Cache for created items
    
    def export(self, workspace_data: WorkspaceData) -> ExportResult:
        """Export workspace data to Miro board"""
        pass
    
    def create_connectors(self, items: List[ItemData], parent_map: Dict[str, List[str]]):
        """Create connectors between parent and child items"""
        pass
```

## 7. Data Models (Pydantic)

### Core Data Hierarchy:
```python
class WorkspaceData(BaseModel):
    id: str
    name: str
    description: Optional[str]
    items: List[ItemData]
    child_workspaces: List[WorkspaceData] = []
    metadata: Dict[str, Any] = {}

class ItemData(BaseModel):
    id: str
    title: str
    description: Optional[str]
    type: str
    status: Optional[str]
    priority: Optional[str]
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    parent_id: Optional[str]
    children_ids: List[str] = []

class ExportResult(BaseModel):
    success: bool
    exported_count: int
    error_count: int
    errors: List[ExportError] = []
    warnings: List[str] = []
    duration: float
```

## 8. Project Structure

```
pyAirfocusExporter/
├── pyairfocusexporter/
│   ├── __init__.py
│   ├── cli.py                    # Click CLI implementation
│   ├── constants.py              # Configuration (gitignored)
│   ├── constants.py.example      # Template configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── workspace.py          # Pydantic models
│   │   ├── item.py
│   │   └── export.py
│   ├── fetcher/
│   │   ├── __init__.py
│   │   ├── airfocus_fetcher.py   # HTTP fetcher
│   │   ├── rate_limiter.py       # Rate limiting logic
│   │   └── cache.py              # Request caching
│   ├── exporter/
│   │   ├── __init__.py
│   │   ├── base_exporter.py      # Abstract base class
│   │   ├── miro_exporter.py      # Miro v2 implementation
│   │   └── factory.py            # Exporter factory
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py            # Structured logging
│   │   ├── progress.py           # Progress bars
│   │   └── validation.py         # Data validation
│   └── __main__.py               # Entry point
├── tests/
│   ├── __init__.py
│   ├── test_fetcher.py
│   ├── test_exporter.py
│   └── test_cli.py
├── .gitignore
├── pyproject.toml                # UV/pip configuration
├── README.md
├── specs.md
└── uv.lock
```

## 9. Development Workflow

### Setup with UV:
```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup project
git clone <repository>
cd pyAirfocusExporter

# Install dependencies
uv sync

# Copy configuration template
cp pyairfocusexporter/constants.py.example pyairfocusexporter/constants.py
# Edit constants.py with your API keys

# Run the tool
uv run pyairfocusexporter export --help
```

### Testing Strategy:
- **Minimal Test Coverage**: ~70% coverage focused on critical paths
- **Unit Tests**: Test fetcher, exporter, and utility functions in isolation
- **Integration Tests**: Test CLI and end-to-end workflows with mock APIs
- **Mocking**: Use `pytest-mock` and `responses` for HTTP mocking
- **Test Structure**:
  ```python
  # Example test structure
  def test_fetcher_rate_limiting():
      """Test that rate limiting is properly enforced"""
      pass
  
  def test_exporter_creates_connectors():
      """Test connector creation with required startItem/endItem"""
      pass
  
  def test_cli_with_dry_run():
      """Test CLI dry-run mode"""
      pass
  ```

## 10. Error Handling and Resilience

### Error Categories:
1. **API Errors**: Handle HTTP status codes, rate limits, and timeouts
2. **Network Errors**: Retry with exponential backoff for transient failures
3. **Data Errors**: Validate data with Pydantic, skip invalid items with warnings
4. **Configuration Errors**: Clear error messages for missing/invalid config

### Retry Logic:
- Exponential backoff: `delay = base_delay * (2 ** attempt)`
- Maximum 3 retries for transient errors

### Logging:
- Structured JSON logging for production
- Colored console output for development
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include `X-Request-Id` in all API request logs
- Progress tracking for large operations

## 11. Performance Optimizations

### Synchronous Architecture:
- Sequential fetching of workspaces
- Batch operations for exporter (create multiple items in single request)
- Connection pooling with httpx

### Memory Management:
- Clear resource cleanup
- Generator patterns for item iteration

## 12. Future Extensibility

### Adding New Exporters:
1. Create new class inheriting from `BaseExporter`
2. Implement required methods: `export()`, `validate_config()`, `cleanup()`
3. Register in `exporter/factory.py`
4. Update CLI help text and validation

### Planned Exporters:
- **CSVExporter**: Export to CSV files for analysis
- **JSONExporter**: Export to JSON format for backup

## 13. Documentation Requirements

### User Documentation:
- `README.md`: Quick start guide and basic usage
- `constants.py.example`: Detailed configuration instructions

### Developer Documentation:
- Code comments following Google style guide
- Type hints for all public APIs
- Docstrings for all modules, classes, and functions
- Architecture decision records (ADRs) for major design choices

### API Documentation:
- OpenAPI/Swagger documentation for internal APIs
- Example requests and responses
- Error code reference

## 14. Security Considerations

### API Key Management:
- Never log API keys in plain text
- Support for environment variables and secret managers
- Prompt for missing credentials with secure input

### Data Protection:
- SSL/TLS for all API communications (with `--ignore-ssl` override)
- No sensitive data in logs or error messages
- Secure disposal of temporary files

### Access Control:
- Validate workspace access before processing
- Check exporter permissions before operations
- Graceful handling of permission errors

---

## Appendix A: Rate Limiting Implementation

```python
import time

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
    
    def acquire(self, tokens: int = 1):
        self._refill()
        while self.tokens < tokens:
            time.sleep(0.1)
            self._refill()
        self.tokens -= tokens
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
```

---

*Last Updated: March 10, 2026*  
*Version: 2.1*  
*Status: Ready for Implementation*
