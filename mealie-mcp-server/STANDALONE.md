# Mealie MCP Server - Standalone Usage

## Running Outside Windsurf

The Mealie MCP Server can run independently outside of Windsurf or any other MCP host.

### Prerequisites

- Python 3.10+
- Mealie API endpoint URL
- Mealie API key

### Quick Start with CLI (Recommended)

The easiest way to run the server is using the CLI wrapper:

```bash
python3 cli.py --base-url https://mealie.example.com --api-key your-api-key-here
```

Or with environment variables:

```bash
export MEALIE_BASE_URL="https://mealie.example.com"
export MEALIE_API_KEY="your-api-key-here"
python3 cli.py
```

#### CLI Options

```bash
python3 cli.py --help
```

Available options:
- `--base-url`: Mealie base URL (without /api suffix)
- `--api-key`: Mealie API key
- `--transport`: MCP transport type (stdio or sse, default: stdio)
- `--port`: Port for SSE transport (default: 8000)
- `--log-level`: Log level (DEBUG, INFO, WARNING, ERROR, default: INFO)
- `--check`: Validate configuration without starting the server
- `--env-file`: Path to custom .env file

#### Examples

```bash
# Validate configuration
python3 cli.py --base-url https://mealie.example.com --api-key xxx --check

# Run with SSE transport
python3 cli.py --base-url https://mealie.example.com --api-key xxx --transport sse --port 8000

# Run with debug logging
python3 cli.py --base-url https://mealie.example.com --api-key xxx --log-level DEBUG

# Use custom .env file
python3 cli.py --env-file /path/to/custom.env
```

### Alternative: Direct Python Invocation

#### Option 1: Environment Variables

```bash
export MEALIE_BASE_URL="https://mealie.example.com"
export MEALIE_API_KEY="your-api-key-here"
python3 run_standalone.py
```

#### Option 2: .env File

Create a `.env` file in the `mealie-mcp-server` directory:

```
MEALIE_BASE_URL=https://mealie.example.com
MEALIE_API_KEY=your-api-key-here
LOG_LEVEL=INFO
```

Then run:

```bash
python3 run_standalone.py
```

#### Option 3: Direct Server Execution

You can also run the server directly:

```bash
cd mealie-mcp-server
python3 src/server.py
```

Or with environment variables inline:

```bash
MEALIE_BASE_URL="https://mealie.example.com" \
MEALIE_API_KEY="your-api-key-here" \
python3 src/server.py
```

### Using with uv

If you prefer using uv for dependency management:

```bash
cd mealie-mcp-server
uv run src/server.py
```

### Configuration Notes

- **Base URL**: Should NOT include `/api` suffix (e.g., `https://mealie.example.com`, not `https://mealie.example.com/api`)
- **API Key**: Long-lived token from Mealie settings
- **Environment variables take precedence** over `.env` file values
- **CLI arguments take precedence** over environment variables

### Transport

The server defaults to stdio transport for MCP communication. To use SSE transport:

```bash
# Via CLI
python3 cli.py --base-url https://mealie.example.com --api-key xxx --transport sse

# Via environment variable
export MCP_TRANSPORT=sse
python3 run_standalone.py
```

### Testing

To test if the server is working correctly:

```bash
# Test connection
curl -H "Authorization: Bearer your-api-key" \
  "https://mealie.example.com/api/app/about"

# Should return JSON with Mealie version info

# Or use CLI to validate configuration
python3 cli.py --base-url https://mealie.example.com --api-key xxx --check
```

### Troubleshooting

#### Connection Refused
- Verify MEALIE_BASE_URL is correct (no `/api` suffix)
- Check network connectivity to Mealie instance
- Verify API key is valid and not expired

#### Import Errors
- Ensure you're running from the `mealie-mcp-server` directory
- Check that Python dependencies are installed

#### Double `/api` in URLs
- Make sure MEALIE_BASE_URL does NOT end with `/api`
- The endpoints already include `/api` prefix
- The CLI will automatically remove `/api` suffix if present

#### Configuration Errors
- Use `--check` flag to validate configuration before starting
- Check CLI output for specific error messages
