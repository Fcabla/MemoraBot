#!/bin/bash
# Run linting and formatting
source .venv/bin/activate
black app/ tests/
ruff check app/ tests/ --fix
mypy app/