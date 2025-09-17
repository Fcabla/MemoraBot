# TICKET-001: Project Setup & Dependencies

**Status:** TODO
**Phase:** 1 - Foundation & Core Infrastructure
**Priority:** High
**Estimated Effort:** 0.5 days

## Detail Section

### Purpose
Set up the complete development environment with all required dependencies and project structure. This forms the foundation for all subsequent development work.

### Business Value
- Ensures consistent development environment across team members
- Provides proper tooling for code quality and testing
- Establishes project conventions early
- Enables rapid development with proper infrastructure

### Acceptance Criteria
- [x] All dependencies installed and locked with UV
- [x] Development scripts created and functional
- [x] Project structure matches specification
- [x] Environment variables configured
- [x] Code quality tools configured

## Implementation Section

### Prerequisites
- Python 3.13 installed
- UV package manager installed
- Git repository initialized

### Dependencies to Install
```bash
# Add to pyproject.toml dependencies
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
jinja2>=3.1.4
python-multipart>=0.0.17
httpx>=0.28.0
pytest>=8.3.0
pytest-cov>=6.0.0
pytest-asyncio>=0.25.0
black>=24.10.0
ruff>=0.8.0
mypy>=1.13.0
python-dotenv>=1.0.1
```

### Files to Create/Modify

#### 1. `/pyproject.toml`
```toml
[project]
name = "memorabot"
version = "0.1.0"
description = "AI-powered file and note management assistant"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "pydantic-ai>=1.0.8",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "jinja2>=3.1.4",
    "python-multipart>=0.0.17",
    "httpx>=0.28.0",
    "python-dotenv>=1.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-cov>=6.0.0",
    "pytest-asyncio>=0.25.0",
    "black>=24.10.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.black]
line-length = 88
target-version = ["py313"]

[tool.ruff]
line-length = 88
target-version = "py313"
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=app --cov-report=term-missing"
```

#### 2. `/.env.example`
```env
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
# Alternative: ANTHROPIC_API_KEY=your_key_here

# Application Settings
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# File Storage
DATA_DIR=./data
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=.txt,.md,.json,.yaml

# Security
SECRET_KEY=your-secret-key-change-this
CORS_ORIGINS=http://localhost:8000
```

#### 3. `/scripts/dev.sh`
```bash
#!/bin/bash
# Development server with auto-reload
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. `/scripts/test.sh`
```bash
#!/bin/bash
# Run tests with coverage
source .venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
```

#### 5. `/scripts/lint.sh`
```bash
#!/bin/bash
# Run linting and formatting
source .venv/bin/activate
black app/ tests/
ruff check app/ tests/ --fix
mypy app/
```

#### 6. `/.gitignore` (append)
```gitignore
# MemoraBot specific
data/
logs/
*.log
.env
*.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Testing
.coverage
htmlcov/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

### Directory Structure to Create
```bash
mkdir -p app
mkdir -p templates
mkdir -p static/css
mkdir -p static/js
mkdir -p tests
mkdir -p data
mkdir -p logs
mkdir -p scripts
```

### Implementation Steps

1. **Update dependencies**
   ```bash
   uv pip install fastapi uvicorn[standard] jinja2 python-multipart httpx python-dotenv
   uv pip install --dev pytest pytest-cov pytest-asyncio black ruff mypy
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with actual API keys
   ```

3. **Make scripts executable**
   ```bash
   chmod +x scripts/*.sh
   ```

4. **Verify installation**
   ```bash
   python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
   python -c "import pydantic_ai; print(f'PydanticAI installed')"
   ```

### Testing
```bash
# Run linting
./scripts/lint.sh

# All checks should pass without errors
```

### Related Files
- `/pyproject.toml` - Project configuration
- `/.env` - Environment variables
- `/scripts/` - Development scripts
- `/.gitignore` - Git ignore rules

### Next Steps
After completion, proceed to TICKET-002 for FastAPI application setup.