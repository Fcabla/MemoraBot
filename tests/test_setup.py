"""Test to verify project setup."""


def test_imports():
    """Test that all required packages can be imported."""
    import fastapi
    import pydantic_ai
    import jinja2
    import httpx
    import dotenv
    import uvicorn

    assert fastapi
    assert pydantic_ai
    assert jinja2
    assert httpx
    assert dotenv
    assert uvicorn


def test_python_version():
    """Test that we're running Python 3.13+."""
    import sys
    assert sys.version_info >= (3, 13)