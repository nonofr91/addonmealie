#!/usr/bin/env python3
"""
Standalone entry point for Mealie MCP Server.

This script allows running the MCP server outside of Windsurf or any other MCP host.
Usage:
    python3 run_standalone.py
    MEALIE_BASE_URL=https://mealie.example.com MEALIE_API_KEY=xxx python3 run_standalone.py
"""
import os
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from server import main

if __name__ == "__main__":
    main()
