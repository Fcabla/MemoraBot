# TICKET-002: FastAPI Application Setup

**Status:** TODO
**Phase:** 1 - Foundation & Core Infrastructure
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** TICKET-001

## Detail Section

### Purpose
Implement the core FastAPI application with proper structure, middleware, error handling, and basic endpoints. This establishes the web framework foundation for the chat interface and API.

### Business Value
- Provides the web server foundation for all user interactions
- Establishes API structure for future extensions
- Ensures proper error handling and logging from the start
- Creates a scalable application architecture

### Acceptance Criteria
- [ ] FastAPI app starts successfully on port 8000
- [ ] Health check endpoint returns 200 OK
- [ ] Jinja2 templates configured and working
- [ ] CORS configured for local development
- [ ] Error handling middleware catches and formats errors
- [ ] Logging system outputs structured logs

## Implementation Section

### Files to Create/Modify

#### 1. `/app/__init__.py`
```python
"""MemoraBot - AI-powered file and note management assistant."""

__version__ = "0.1.0"
```

#### 2. `/app/main.py`
```python
"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.logging import setup_logging
from app.middleware import error_handler_middleware
from app.routers import chat, health

# Setup logging
logger = setup_logging()

# Template configuration
templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MemoraBot application")

    # Ensure data directory exists
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down MemoraBot application")


# Create FastAPI app
app = FastAPI(
    title="MemoraBot",
    description="AI-powered file and note management assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware
app.middleware("http")(error_handler_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main chat interface."""
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "app_name": "MemoraBot"}
    )
```

#### 3. `/app/config.py`
```python
"""Application configuration management."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = Field(default="development")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")

    # LLM Configuration
    LLM_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)

    # File Storage
    DATA_DIR: str = Field(default="./data")
    MAX_FILE_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: str = Field(default=".txt,.md,.json,.yaml")

    # Security
    SECRET_KEY: str = Field(default="change-this-secret-key")
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:8000"])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_file_extensions(self) -> set[str]:
        """Parse allowed file types into a set."""
        return set(self.ALLOWED_FILE_TYPES.split(","))

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Create global settings instance
settings = Settings()
```

#### 4. `/app/logging.py`
```python
"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.config import settings


def setup_logging() -> logging.Logger:
    """Configure application logging."""

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Configure root logger
    logger = logging.getLogger("memorabot")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove default handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/memorabot.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
```

#### 5. `/app/middleware.py`
```python
"""Custom middleware for the application."""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger("memorabot")


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Global error handler middleware."""
    start_time = time.time()

    try:
        response = await call_next(request)

        # Log request
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {process_time:.3f}s"
        )

        return response

    except Exception as e:
        # Log error
        logger.error(
            f"Error processing request {request.method} {request.url.path}: {str(e)}",
            exc_info=True
        )

        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(e) if logger.level == logging.DEBUG else "An error occurred",
                "path": str(request.url.path)
            }
        )
```

#### 6. `/app/routers/__init__.py`
```python
"""API routers package."""
```

#### 7. `/app/routers/health.py`
```python
"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    from app import __version__
    from app.config import settings

    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.APP_ENV
    )


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check for deployment."""
    # Check critical dependencies
    checks = {
        "database": True,  # Placeholder for future DB check
        "llm_configured": bool(
            settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY
        ),
        "data_directory": Path(settings.DATA_DIR).exists(),
    }

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks
    }
```

#### 8. `/app/routers/chat.py`
```python
"""Chat interface API endpoints."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""
    content: str
    role: str = "user"
    timestamp: Optional[datetime] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    role: str = "assistant"
    timestamp: datetime
    tool_calls: Optional[list] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessage) -> ChatResponse:
    """Process a chat message."""
    # Placeholder for agent processing
    return ChatResponse(
        message=f"Echo: {message.content}",
        role="assistant",
        timestamp=datetime.now(),
        tool_calls=None
    )


@router.get("/history")
async def get_chat_history() -> list[dict]:
    """Get chat history for the current session."""
    # Placeholder - will be implemented with session management
    return []


@router.delete("/clear")
async def clear_chat() -> dict:
    """Clear the current chat session."""
    # Placeholder - will be implemented with session management
    return {"status": "cleared"}
```

#### 9. `/templates/base.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MemoraBot{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='/css/main.css') }}">
    {% block extra_head %}{% endblock %}
</head>
<body>
    <div class="app-container">
        {% block content %}{% endblock %}
    </div>

    <script src="{{ url_for('static', path='/js/main.js') }}"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

#### 10. `/templates/chat.html`
```html
{% extends "base.html" %}

{% block title %}MemoraBot - Chat{% endblock %}

{% block content %}
<div class="chat-container">
    <header class="chat-header">
        <h1>🗂️ MemoraBot</h1>
        <p>Your AI File & Note Assistant</p>
    </header>

    <div class="chat-messages" id="chat-messages">
        <div class="message assistant">
            <div class="message-content">
                Hello! I'm MemoraBot, your intelligent file and note assistant.
                I can help you organize, manage, and interact with your files through natural language.
                What would you like to do today?
            </div>
        </div>
    </div>

    <div class="chat-input-container">
        <textarea
            id="message-input"
            class="message-input"
            placeholder="Type your message here..."
            rows="3"
        ></textarea>
        <button id="send-button" class="send-button">Send</button>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{{ url_for('static', path='/js/chat.js') }}"></script>
{% endblock %}
```

### Testing Steps

1. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Test health endpoint**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","version":"0.1.0","environment":"development"}
   ```

3. **Test main page**
   - Navigate to http://localhost:8000
   - Should see the chat interface

4. **Test chat endpoint**
   ```bash
   curl -X POST http://localhost:8000/chat/message \
     -H "Content-Type: application/json" \
     -d '{"content":"Hello"}'
   ```

### Verification Checklist
- [ ] Application starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Main page renders chat interface
- [ ] Static files are served correctly
- [ ] Logs are written to logs/memorabot.log
- [ ] CORS headers are present in responses
- [ ] Error middleware catches exceptions

### Related Files
- `/app/main.py` - Main application
- `/app/config.py` - Configuration management
- `/app/logging.py` - Logging setup
- `/app/middleware.py` - Custom middleware
- `/app/routers/` - API endpoints
- `/templates/` - HTML templates

### Next Steps
After completion, proceed to TICKET-003 for PydanticAI agent setup.