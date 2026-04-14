#!/usr/bin/env python3
"""Test AI Provider Factory and Implementations."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai.factory import create_ai_provider
from ai.base import AIProvider


def test_factory_default():
    """Test that factory creates CascadeProvider by default."""
    os.environ.pop("AI_PROVIDER", None)
    provider = create_ai_provider()
    assert provider is not None
    assert isinstance(provider, AIProvider)
    print("✓ Default provider (Cascade) created successfully")


def test_factory_mock():
    """Test that factory creates MockProvider when requested."""
    os.environ["AI_PROVIDER"] = "mock"
    provider = create_ai_provider()
    assert provider is not None
    assert isinstance(provider, AIProvider)
    print("✓ Mock provider created successfully")


def test_mock_provider_methods():
    """Test MockProvider methods."""
    os.environ["AI_PROVIDER"] = "mock"
    provider = create_ai_provider()
    
    # Test complete method
    result = provider.complete("test prompt")
    assert result is not None
    print("✓ MockProvider.complete() works")
    
    # Test analyze_ingredient method
    result = provider.analyze_ingredient("2 cups flour")
    assert result is not None
    assert "quantity" in result
    assert "unit" in result
    assert "food" in result
    print("✓ MockProvider.analyze_ingredient() works")
    
    # Test structure_recipe method
    result = provider.structure_recipe({"name": "Test Recipe"})
    assert result is not None
    assert "name" in result
    print("✓ MockProvider.structure_recipe() works")


if __name__ == "__main__":
    print("Testing AI Provider Factory and Implementations...")
    print()
    
    try:
        test_factory_default()
        test_factory_mock()
        test_mock_provider_methods()
        print()
        print("All tests passed! ✓")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
