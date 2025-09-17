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