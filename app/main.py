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
    allow_origins=settings.cors_origins_list,
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