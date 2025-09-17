#!/bin/bash
# Run tests with coverage
source .venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html