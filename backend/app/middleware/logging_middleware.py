import logging
import time

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
TRANSFER_COUNT = Counter(
    "transfer_total",
    "Total transfers",
    ["status"],
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        path = request.url.path
        if path != "/metrics":
            REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
            REQUEST_LATENCY.labels(request.method, path).observe(duration_ms / 1000)

        logger.info(
            "request.completed",
            extra={
                "structured": {
                    "event": "request.completed",
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            },
        )
        return response
