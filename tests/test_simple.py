"""
Simple test to verify testing infrastructure
"""
import pytest


def test_basic_functionality():
    """Basic test to verify pytest is working"""
    assert True
    assert 1 + 1 == 2
    assert "hello" + " world" == "hello world"


def test_environment_variables():
    """Test that environment variables are set correctly"""
    import os
    
    # Check that test environment variables are set
    assert os.environ.get("ENVIRONMENT") == "development"
    assert os.environ.get("SECRET_KEY") == "test-secret-key-for-testing-only"
    assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"
    assert os.environ.get("USE_MOCK_SMS") == "true"


def test_imports():
    """Test that we can import basic modules"""
    # Test basic imports
    import sqlalchemy
    import pytest
    import asyncio
    
    assert sqlalchemy.__version__ is not None
    assert pytest.__version__ is not None


@pytest.mark.unit
def test_unit_marker():
    """Test that unit markers work"""
    assert True


@pytest.mark.slow
def test_slow_marker():
    """Test that slow markers work"""
    assert True


@pytest.mark.smoke
def test_smoke_marker():
    """Test that smoke markers work"""
    assert True
