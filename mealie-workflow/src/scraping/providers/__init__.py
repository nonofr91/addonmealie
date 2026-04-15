#!/usr/bin/env python3
"""
Package des providers de scraping
"""

from .jina_mcp_provider import JinaMCPProvider
from .requests_provider import RequestsProvider

__all__ = ['JinaMCPProvider', 'RequestsProvider']
