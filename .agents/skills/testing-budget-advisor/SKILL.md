# Testing: Budget Advisor Docker Addon

How to test Docker image changes for the `mealie-budget-advisor` addon.

## Prerequisites

- Docker installed and running
- Access to `ghcr.io/nonofr91/mealie-budget-advisor` (public, no auth needed for pulls)

## Devin Secrets Needed

None for healthcheck/Docker testing. The API container needs `MEALIE_API_KEY` and `MEALIE_BASE_URL` env vars to start, but dummy values work for healthcheck-only validation.

## Build the Image Locally

```bash
cd addons/mealie-budget-advisor
docker build -t mealie-budget-advisor:<version>-test .
```

Build takes ~60s due to pip install of Python dependencies.

## Testing Healthchecks

### API healthcheck (port 8003)

```bash
# Start API container (needs env vars)
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
# Start UI container
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

### Comparing old vs new image

To prove a fix works, pull the old published image and compare:

```bash
# Pull old image
docker pull ghcr.io/nonofr91/mealie-budget-advisor:<old-version>

# Check if a binary exists
docker run --rm ghcr.io/nonofr91/mealie-budget-advisor:<old-version> which curl
# If missing: exit code 1, no output

# Check in new image
docker run --rm mealie-budget-advisor:<new-version>-test which curl
# If present: exit code 0, output /usr/bin/curl
```

## Cleanup

```bash
docker rm -f test-ui test-api 2>/dev/null
```

## Common Issues

- **API container crashes on startup**: It requires `MEALIE_API_KEY` env var. Pass a dummy value for healthcheck-only testing.
- **Streamlit takes ~15s to start**: Don't run healthcheck immediately after `docker run`. Wait at least 15 seconds.
- **Base image `python:3.11-slim`**: Does NOT include `curl`, `wget`, or `requests` by default. Any healthcheck using these must explicitly install them in the Dockerfile.
- **Version governance (AGENTS.md)**: When bumping the Docker image version, the `pyproject.toml` version AND all `docker-compose*.yml` image tags must be updated in the same commit.
- **Tag 0.2.0 was never published to ghcr.io**: If you need to compare against the previous version, 0.1.1 is the latest published image as of this writing. This might change in the future.

## Testing is Shell-Only

All healthcheck testing is done via `docker run`/`docker exec` commands. No browser or GUI interaction needed. No screen recording required.
