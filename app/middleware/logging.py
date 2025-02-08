from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import time
import uuid
from app.util.logger import setup_logger, set_correlation_id

logger = setup_logger("middleware.logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Start timing the request
        start_time = time.time()

        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        correlation_id = set_correlation_id(correlation_id)

        # Log the incoming request
        logger.info(
            f"Incoming {request.method} request to {request.url.path}",
            extra={
                "data": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_host": request.client.host if request.client else None,
                    "correlation_id": correlation_id,
                }
            },
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Log the response
            logger.info(
                f"Completed {request.method} request to {request.url.path}",
                extra={
                    "data": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration": f"{duration:.3f}s",
                        "correlation_id": correlation_id,
                    }
                },
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            # Log any unhandled exceptions
            logger.error(
                f"Error processing {request.method} request to {request.url.path}",
                extra={
                    "data": {
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                },
            )
            raise  # Re-raise the exception to be handled by FastAPI's exception handlers
