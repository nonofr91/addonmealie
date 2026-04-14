#!/usr/bin/env python3
"""Test AI Recipe Analyzer Integration."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Set AI_PROVIDER to mock for testing
os.environ["AI_PROVIDER"] = "mock"

from ai.recipe_analyzer import AIRecipeAnalyzer


def test_ai_recipe_analyzer_init():
    """Test that AIRecipeAnalyzer initializes correctly."""
    analyzer = AIRecipeAnalyzer()
    assert analyzer.ai_provider is not None
    print("✓ AIRecipeAnalyzer initialized successfully")


def test_ai_recipe_analyzer_analyze_ingredient():
    """Test that AIRecipeAnalyzer can analyze ingredients."""
    analyzer = AIRecipeAnalyzer()
    result = analyzer.analyze_ingredient("2 cups flour")
    assert result is not None
    assert "quantity" in result
    assert "unit" in result
    assert "food" in result
    print("✓ AIRecipeAnalyzer.analyze_ingredient() works")


def test_ai_recipe_analyzer_structure_recipe():
    """Test that AIRecipeAnalyzer can structure recipes."""
    analyzer = AIRecipeAnalyzer()
    result = analyzer.structure_recipe({"name": "Test Recipe"})
    assert result is not None
    assert "name" in result
    print("✓ AIRecipeAnalyzer.structure_recipe() works")


def test_ai_recipe_analyzer_analyze_and_parse():
    """Test that AIRecipeAnalyzer can analyze and parse content."""
    analyzer = AIRecipeAnalyzer()
    content = "<h1>Test Recipe</h1><p>A simple test recipe.</p>"
    result = analyzer.analyze_and_parse(content, "http://example.com")
    assert result is not None
    assert "name" in result
    print("✓ AIRecipeAnalyzer.analyze_and_parse() works")


if __name__ == "__main__":
    print("Testing AI Recipe Analyzer Integration...")
    print()
    
    try:
        test_ai_recipe_analyzer_init()
        test_ai_recipe_analyzer_analyze_ingredient()
        test_ai_recipe_analyzer_structure_recipe()
        test_ai_recipe_analyzer_analyze_and_parse()
        print()
        print("All AI Recipe Analyzer tests passed! ✓")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
