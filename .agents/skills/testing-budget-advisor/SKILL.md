# Testing: Mealie Budget Advisor

How to test the `mealie-budget-advisor` addon locally using Docker and a mock Mealie server.

## Prerequisites

- Docker installed and running
- Access to `ghcr.io/nonofr91/mealie-budget-advisor` (public, no auth needed for pulls)

## Devin Secrets Needed

No secrets required for local testing. The mock server provides its own auth tokens.
For healthcheck-only validation, dummy values work for `MEALIE_API_KEY`.

## Environment Variables

The budget-advisor requires these env vars to start:

| Variable | Required | Description |
|---|---|---|
| `MEALIE_BASE_URL` | Yes | URL of the Mealie instance (or mock) |
| `MEALIE_API_KEY` | Yes | API token (any non-empty string for mock) |
| `ADDON_API_URL` | No | URL of the addon API (default: http://localhost:8003) — used by the Streamlit UI |
| `ADDON_API_PORT` | No | API port (default: 8003) |
| `ADDON_UI_PORT` | No | UI port (default: 8503) |

## Docker Image

- The Docker CMD is `uvicorn mealie_budget_advisor.api:app --host 0.0.0.0 --port 8003`
- To override the port, pass the full uvicorn command: `uvicorn mealie_budget_advisor.api:app --host 0.0.0.0 --port <PORT>`
- Do NOT use `python3 -m mealie_budget_advisor.api` — the api module has no `__main__` block
- The CLI entry point is `mealie-budget` (e.g., `mealie-budget sync-cost <slug>`)

## Build the Image Locally

```bash
cd addons/mealie-budget-advisor
docker build -t mealie-budget-advisor:<version>-test .
```

Build takes ~60s due to pip install of Python dependencies.

## Mock Mealie Server

For isolated testing, create a simple Python HTTP server that responds to:

- `GET /api/app/about` → `{"version": "1.0.0-mock"}`
- `GET /api/recipes?page=X&perPage=Y` → `{"items": [...], "total": <N>, "page": X, "per_page": Y}`
- `GET /api/recipes/<slug>` → Full recipe object with `recipeIngredient`, `extras`, `recipeYield`
- `POST /api/auth/token` → `{"access_token": "mock-token", "token_type": "bearer"}`
- `PATCH /api/recipes/<slug>` → `{"success": true}` (for publishing costs to extras)
- `GET /api/foods` → `{"items": [], "total": 0}`
- `GET /api/units` → `{"items": [], "total": 0}`
- `GET /health` → `{"status": "ok"}`

The mock should return **at least 5 recipes** with distinct names and slugs to test dropdown/multiselect widgets.

The `total` field in the `/api/recipes` response is the pagination metadata that `get_recipe_count()` reads. Set it to a known value (e.g., 42) and verify the `/status` endpoint returns that same count.

## Testing Healthchecks

### API healthcheck (port 8003)

```bash
docker run -d --name test-api \
  -e MEALIE_API_KEY=test-dummy-key \
  -e MEALIE_BASE_URL=http://localhost:9999 \
  mealie-budget-advisor:<version>-test \
  uvicorn mealie_budget_advisor.api:app --host 0.0.0.0 --port 8003

# Wait 5s for startup, then test
docker exec test-api curl -f http://localhost:8003/health
# Expected: {"status":"ok","service":"mealie-budget-advisor"}
```

### Streamlit UI healthcheck (port 8503)

```bash
docker run -d --name test-ui \
  mealie-budget-advisor:<version>-test \
  sh -c "streamlit run mealie_budget_advisor/ui.py \
    --server.port=8503 --server.address=0.0.0.0 \
    --server.headless=true --browser.gatherUsageStats=false \
    --server.fileWatcherType=none"

# Wait 15s for Streamlit startup (slower than uvicorn), then test
docker exec test-ui curl -f http://localhost:8503/_stcore/health
# Expected: "ok"
```

## Testing API Behavior (with Mock)

### Testing Workflow

1. Start mock Mealie server on a local port (e.g., 9925)
2. Run the Docker container with `--network host` so it can reach the mock
3. Call `GET /status` and verify the response JSON
4. For comparison tests: run old and new images on different ports against the same mock

### Comparing old vs new image

```bash
# Pull old image
docker pull ghcr.io/nonofr91/mealie-budget-advisor:<old-version>

# Check if a binary exists
docker run --rm ghcr.io/nonofr91/mealie-budget-advisor:<old-version> which curl

# Check in new image
docker run --rm mealie-budget-advisor:<new-version>-test which curl
```

## Testing the UI (Browser-Based)

For UI changes (e.g., dropdowns, buttons, tab rendering), test via Streamlit in the browser:

### Local Development Mode (faster iteration)

```bash
cd addons/mealie-budget-advisor
pip install -e "."

# Start mock Mealie + API + UI
python3 /path/to/mock_mealie.py &   # port 9925
MEALIE_BASE_URL=http://localhost:9925 MEALIE_API_KEY=test-key \
  uvicorn mealie_budget_advisor.api:app --host 0.0.0.0 --port 8003 &
ADDON_API_URL=http://localhost:8003 MEALIE_BASE_URL=http://localhost:9925 \
  python3 -m streamlit run src/mealie_budget_advisor/ui.py \
  --server.port=8504 --server.address=0.0.0.0 \
  --server.headless=true --browser.gatherUsageStats=false \
  --server.fileWatcherType=none &
```

Then open `http://localhost:8504` in the browser and use computer-use tools to interact with the UI.

### UI Test Checklist

- **Statut tab**: Shows recipe count, connection status, feature flags
- **Budget tab**: Budget form and history
- **Planning tab**: Shows warning if no budget defined; does NOT block other tabs
- **Prix tab**: Open Prices search + manual price form
- **Coûts tab**: Recipe selectbox (names, not slugs), batch cost button, comparison multiselect

## Unit Testing (No Docker Needed)

For logic-level fixes (ingredient dedup, time parsing, cost PATCH), unit tests are faster and more adversarial than Docker-based tests.

### Testing ingredient deduplication (UUID fix)

The `MatchResult` dataclass in `mealie-workflow/src/importing/ingredient_matcher.py` has:
- `match_id`: the Mealie UUID (e.g., `b31086b3-029f-415d-8d1d-435358fb297c`)
- `matched_item`: the full dict with `{'id': ..., 'name': 'ail'}`

To test that dedup uses the **name** (not UUID), create a `MatchResult` with both fields set and verify the importer reads `matched_item.get('name', ...)`. The adversarial check: verify the OLD code path (`match_id`) would produce the UUID — this proves the test distinguishes broken from fixed code.

```python
import sys
sys.path.insert(0, 'repos/addonmealie/mealie-workflow/src')
from importing.ingredient_matcher import MatchResult

match = MatchResult(
    matched=True,
    matched_item={'id': 'b31086b3-...', 'name': 'ail'},
    similarity=0.95,
    match_id='b31086b3-...'
)
# FIXED: food = match.matched_item.get('name', fallback)
# BROKEN: food = match.match_id  → UUID in ingredient text
```

### Testing ISO 8601 duration parsing

`RequestsProvider._parse_iso_duration` is a static method — import and call directly:

```python
from scraping.providers.requests_provider import RequestsProvider
assert RequestsProvider._parse_iso_duration('PT1H30M') == '90'
assert RequestsProvider._parse_iso_duration(None) is None
assert RequestsProvider._parse_iso_duration('PT0M') is None  # zero → None
```

### Testing atomic cost PATCH

`MealieClient.patch_cost_data` should send exactly **1 PATCH** with both `extras` and `notes`. Mock `get_recipe` and `session.patch`, then assert:
1. `session.patch.call_count == 1`
2. JSON body has both `"extras"` and `"notes"` keys
3. Existing cost notes are updated in-place (not duplicated)
4. Non-cost notes are preserved unchanged

### Running existing repo tests

```bash
cd addons/mealie-budget-advisor
python3 -m pytest tests/test_cost_sync.py -v
```

These tests mock `patch_cost_data` (not the old `patch_extras`). If tests fail with `AttributeError: patch_extras`, the test file needs updating to match the current API.

## Key Endpoints to Test

| Endpoint | Method | What it does |
|---|---|---|
| `/status` | GET | System status, recipe count, feature flags |
| `/health` | GET | Simple health check |
| `/recipes/list` | GET | Returns `[{name, slug}]` for UI dropdowns |
| `/recipes/refresh-costs` | POST | Recalculate costs for all recipes |
| `/recipes/{slug}/cost` | GET | Get cost for a specific recipe |
| `/recipes/{slug}/sync-cost` | POST | Publish cost to Mealie extras |

## Config Singleton Caveat

`BudgetConfig` is a singleton (`config.py`). If running multiple containers on the same host, use separate Docker containers (not processes) to avoid config pollution. Each container gets its own Python runtime.

## Common Issues

- **Container exits immediately**: Check `docker logs <name>` — usually a missing `MEALIE_API_KEY` env var
- **Streamlit takes ~15s to start**: Don't run healthcheck immediately after `docker run`. Wait at least 15 seconds.
- **Base image `python:3.11-slim`**: Does NOT include `curl`, `wget`, or `requests` by default. Any healthcheck using these must explicitly install them in the Dockerfile.
- **Cannot reach mock from container**: Use `--network host` or set `MEALIE_BASE_URL` to `http://host.docker.internal:<port>` on Docker Desktop
- **Live Coolify instance unreachable from Devin VM**: Network routes may not exist. Pivot to local Docker testing instead.
- **Version governance (AGENTS.md)**: When bumping the Docker image version, the `pyproject.toml` version AND all `docker-compose*.yml` image tags must be updated in the same commit.
- **`st.stop()` in Streamlit tabs**: Never use `st.stop()` inside a tab context — it halts the **entire script**, preventing all subsequent tabs from rendering. Use `if/else` blocks instead to conditionally show/hide content within a tab.
- **Streamlit `@st.cache_data` returns empty list**: If the API is unreachable when the cache is first populated, it will cache an empty list for the TTL duration. This can cause dropdowns to appear empty. Restart Streamlit or wait for the TTL to expire.
- **`mealie-workflow` imports in unit tests**: The workflow module uses relative imports and has heavy dependencies. Use `sys.path.insert(0, 'mealie-workflow/src')` only in standalone test scripts — not in installed packages (see AGENTS.md).
- **Pydantic field name clashes**: Avoid naming a field the same as its type (e.g., `date: date`). Pydantic 2.13+ rejects this even without `from __future__ import annotations`. Rename the field and use `alias=` for JSON compatibility.

## Cleanup

```bash
docker rm -f test-ui test-api 2>/dev/null
```
