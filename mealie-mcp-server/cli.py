#!/usr/bin/env python3
"""
CLI wrapper for Mealie MCP Server.

Provides a user-friendly command-line interface with configuration validation.
"""
import argparse
import os
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


def validate_url(url: str) -> str:
    """Validate and normalize Mealie base URL."""
    if not url:
        raise ValueError("Base URL is required")
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Ensure it's not including /api suffix (endpoints add it)
    if url.endswith('/api'):
        print("Warning: Base URL should not include '/api' suffix. Removing it.")
        url = url[:-4]
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError("Base URL must start with http:// or https://")
    
    return url


def validate_api_key(api_key: str) -> str:
    """Validate Mealie API key."""
    if not api_key:
        raise ValueError("API key is required")
    
    # Basic validation - JWT tokens are typically long strings with dots
    if len(api_key) < 20:
        raise ValueError("API key appears to be too short")
    
    return api_key


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Mealie MCP Server - Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with environment variables
  MEALIE_BASE_URL=https://mealie.example.com MEALIE_API_KEY=xxx python3 cli.py
  
  # Run with command-line arguments
  python3 cli.py --base-url https://mealie.example.com --api-key xxx
  
  # Run with SSE transport
  python3 cli.py --base-url https://mealie.example.com --api-key xxx --transport sse
  
  # Run with debug logging
  python3 cli.py --base-url https://mealie.example.com --api-key xxx --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--base-url',
        dest='base_url',
        help='Mealie base URL (without /api suffix). Can also use MEALIE_BASE_URL env var.'
    )
    
    parser.add_argument(
        '--api-key',
        dest='api_key',
        help='Mealie API key. Can also use MEALIE_API_KEY env var.'
    )
    
    parser.add_argument(
        '--transport',
        choices=['stdio', 'sse'],
        default='stdio',
        help='MCP transport type (default: stdio)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for SSE transport (default: 8000)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Only check configuration without starting the server'
    )
    
    parser.add_argument(
        '--env-file',
        help='Path to .env file (default: .env in current directory)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables from .env file if specified
    if args.env_file:
        from dotenv import load_dotenv
        env_path = Path(args.env_file)
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment from {env_path}")
        else:
            print(f"Error: Environment file not found: {env_path}")
            sys.exit(1)
    
    # Get configuration from command line or environment variables
    base_url = args.base_url or os.getenv('MEALIE_BASE_URL')
    api_key = args.api_key or os.getenv('MEALIE_API_KEY')
    
    # Validate configuration
    try:
        base_url = validate_url(base_url)
        api_key = validate_api_key(api_key)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nTip: Set MEALIE_BASE_URL and MEALIE_API_KEY environment variables")
        print("or use --base-url and --api-key command-line arguments.")
        sys.exit(1)
    
    # Set environment variables for the server
    os.environ['MEALIE_BASE_URL'] = base_url
    os.environ['MEALIE_API_KEY'] = api_key
    os.environ['MCP_TRANSPORT'] = args.transport
    os.environ['LOG_LEVEL'] = args.log_level
    
    if args.transport == 'sse':
        os.environ['MCP_PORT'] = str(args.port)
    
    # If check mode, just validate and exit
    if args.check:
        print("✓ Configuration is valid")
        print(f"  Base URL: {base_url}")
        print(f"  Transport: {args.transport}")
        if args.transport == 'sse':
            print(f"  Port: {args.port}")
        return
    
    # Import and run the server
    try:
        from server import main as server_main
        print(f"Starting Mealie MCP Server...")
        print(f"  Base URL: {base_url}")
        print(f"  Transport: {args.transport}")
        if args.transport == 'sse':
            print(f"  Port: {args.port}")
        print()
        server_main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
