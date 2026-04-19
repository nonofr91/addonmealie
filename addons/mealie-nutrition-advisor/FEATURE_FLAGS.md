# Feature Flags - Mealie Nutrition Advisor

## Overview

The Mealie Nutrition Advisor supports feature flags to enable or disable specific functionalities at runtime. This allows for flexible deployment and testing of different configurations without modifying the code.

## Available Feature Flags

### `ENABLE_PROFILE_UI` (default: `true`)

Enables or disables the profile management UI and API endpoints.

**When enabled:**
- Profile management tab is visible in the UI
- API endpoints for profiles are accessible:
  - `GET /profiles`
  - `GET /profiles/{name}`
  - `POST /profiles`
  - `PUT /profiles/{name}`
  - `DELETE /profiles/{name}`
  - `POST /profiles/{name}/presence`

**When disabled:**
- Profile management tab is hidden
- Profile API endpoints return 503 (Service Unavailable)
- Error message: "Profile UI feature is disabled"

**Use case:** Disable if you only need nutrition analysis without profile management.

---

### `ENABLE_MENU_PLANNER` (default: `true`)

Enables or disables the menu planning functionality.

**When enabled:**
- Menu planning features are available
- Conflict detection is active (if `ENABLE_CONFLICT_DETECTION` is also true)

**When disabled:**
- Menu planning features are hidden
- Menu planning API endpoints return 503

**Use case:** Disable if you only need profile management and nutrition analysis.

---

### `ENABLE_NUTRITION_ANALYSIS` (default: `true`)

Enables or disables the nutrition analysis and enrichment features.

**When enabled:**
- Nutrition enrichment tab is visible in the UI
- API endpoints for nutrition are accessible:
  - `GET /nutrition/scan`
  - `POST /nutrition/enrich`
  - `POST /nutrition/recipe/{slug}`

**When disabled:**
- Nutrition enrichment tab is hidden
- Nutrition API endpoints return 503
- Error message: "Nutrition analysis feature is disabled"

**Use case:** Disable if you only need profile management without nutrition analysis.

---

### `ENABLE_CONFLICT_DETECTION` (default: `true`)

Enables or disables the multi-profile conflict detection in menu planning.

**When enabled:**
- Conflict detection is active during menu planning
- Conflicts are logged and reported in the menu JSON
- Recipes with low household scores (< 0.5) are rejected

**When disabled:**
- Conflict detection is skipped
- All recipes are considered regardless of profile conflicts

**Use case:** Disable if you don't need conflict detection or want to manually handle conflicts.

---

## Configuration

### Environment Variables

Feature flags can be configured via environment variables:

```bash
# Enable all features (default)
ENABLE_PROFILE_UI=true
ENABLE_MENU_PLANNER=true
ENABLE_NUTRITION_ANALYSIS=true
ENABLE_CONFLICT_DETECTION=true

# Disable specific features
ENABLE_PROFILE_UI=false
ENABLE_MENU_PLANNER=false
ENABLE_NUTRITION_ANALYSIS=false
ENABLE_CONFLICT_DETECTION=false
```

### Docker Compose

In `docker-compose.yml`, feature flags are set with defaults:

```yaml
services:
  nutrition-api:
    environment:
      - ENABLE_PROFILE_UI=${ENABLE_PROFILE_UI:-true}
      - ENABLE_MENU_PLANNER=${ENABLE_MENU_PLANNER:-true}
      - ENABLE_NUTRITION_ANALYSIS=${ENABLE_NUTRITION_ANALYSIS:-true}
      - ENABLE_CONFLICT_DETECTION=${ENABLE_CONFLICT_DETECTION:-true}

  nutrition-ui:
    environment:
      - ENABLE_PROFILE_UI=${ENABLE_PROFILE_UI:-true}
      - ENABLE_MENU_PLANNER=${ENABLE_MENU_PLANNER:-true}
      - ENABLE_NUTRITION_ANALYSIS=${ENABLE_NUTRITION_ANALYSIS:-true}
```

### .env File

Create a `.env` file in the addon directory:

```bash
MEALIE_BASE_URL=http://localhost:9925
MEALIE_API_KEY=your-api-key
ADDON_SECRET_KEY=test

# Feature flags
ENABLE_PROFILE_UI=true
ENABLE_MENU_PLANNER=true
ENABLE_NUTRITION_ANALYSIS=true
ENABLE_CONFLICT_DETECTION=true
```

## Common Configurations

### Full Feature Set (Default)

All features enabled:

```bash
ENABLE_PROFILE_UI=true
ENABLE_MENU_PLANNER=true
ENABLE_NUTRITION_ANALYSIS=true
ENABLE_CONFLICT_DETECTION=true
```

### Profiles Only

Only profile management, no nutrition analysis or menu planning:

```bash
ENABLE_PROFILE_UI=true
ENABLE_MENU_PLANNER=false
ENABLE_NUTRITION_ANALYSIS=false
ENABLE_CONFLICT_DETECTION=false
```

### Nutrition Analysis Only

Only nutrition enrichment, no profiles or menu planning:

```bash
ENABLE_PROFILE_UI=false
ENABLE_MENU_PLANNER=false
ENABLE_NUTRITION_ANALYSIS=true
ENABLE_CONFLICT_DETECTION=false
```

### Profiles + Menu Planning (No Nutrition Analysis)

Profile management and menu planning without nutrition enrichment:

```bash
ENABLE_PROFILE_UI=true
ENABLE_MENU_PLANNER=true
ENABLE_NUTRITION_ANALYSIS=false
ENABLE_CONFLICT_DETECTION=true
```

## Implementation Details

### API Level

Feature flags are checked in the API endpoints before processing requests:

```python
config = _get_config()
if not config.enable_profile_ui:
    raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
```

### UI Level

Feature flags are checked in the Streamlit UI to conditionally show tabs:

```python
tabs = []
if ENABLE_NUTRITION_ANALYSIS:
    tabs.append("🔬 Enrichissement")
if ENABLE_PROFILE_UI:
    tabs.append("👥 Profils")
tabs.append("📊 Statut")
```

### Planner Level

The `ENABLE_CONFLICT_DETECTION` flag is used in the menu planner to control conflict detection:

```python
if config.enable_conflict_detection:
    has_conflict, conflict_msg, individual_scores = self._check_multi_profile_conflict(...)
```

## Status Display

The Status tab in the UI displays the current state of all feature flags:

```
Feature Flags actifs
- Profile UI: ✅ Activé
- Menu Planner: ✅ Activé
- Nutrition Analysis: ✅ Activé
```

## Migration Guide

If you're upgrading from a version without feature flags:

1. **No action required**: All features are enabled by default
2. **Optional**: Configure feature flags in your `.env` file to customize the addon behavior
3. **Recommended**: Review the feature flags and disable any features you don't need to reduce resource usage

## Troubleshooting

### Feature Not Working

If a feature is not working despite the flag being enabled:

1. Check the environment variables are set correctly
2. Verify the flags are passed to both the API and UI containers
3. Check the logs for any errors related to the feature
4. Ensure the flag is set before the container starts

### UI Shows Wrong State

If the UI shows the wrong state for feature flags:

1. Restart the UI container after changing flags
2. Check the environment variables in the UI container
3. Verify the `.env` file is loaded correctly

### API Returns 503

If the API returns 503 for a feature:

1. Check the corresponding feature flag is enabled
2. Verify the API container has the correct environment variables
3. Restart the API container after changing flags
