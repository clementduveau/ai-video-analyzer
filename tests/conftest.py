"""Shared pytest configuration and fixtures for all tests.

This module provides session-level fixtures including:
- Automatic cleanup of test artifacts after test session completion
"""
import pytest
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Clean up test result files after all tests complete.
    
    This fixture runs automatically after the entire test session ends.
    Removes JSON result files created during testing to prevent accumulation.
    """
    yield  # Let all tests run first
    
    # Cleanup after all tests complete
    results_dir = Path(__file__).parent.parent / "results"
    
    if not results_dir.exists():
        return
    
    # Patterns for test-generated result files
    test_patterns = [
        "*Test_*.json",
        "*test_*.json", 
        "*Integration_*.json",
        "*Persist_*.json",
        "integration_*.json",
        "persist_*.json"
    ]
    
    cleaned_count = 0
    for pattern in test_patterns:
        for result_file in results_dir.glob(pattern):
            try:
                result_file.unlink()
                cleaned_count += 1
            except Exception:
                pass  # Silently ignore cleanup failures
    
    if cleaned_count > 0:
        print(f"\n✓ Cleaned up {cleaned_count} test result file(s)")
