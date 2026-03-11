import logging
import shutil
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import router
from app.api.websocket import ws_router
from app.config import settings

logger = logging.getLogger(__name__)

__version__ = "0.5.0"
MAX_JOB_AGE_SECONDS = 24 * 60 * 60  # 24 hours
_RATE_LIMIT_CLEANUP_INTERVAL = 300  # Evict stale IPs every 5 minutes


# ── Security Headers ───────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
        return response


# ── Rate Limiter ────────────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter for upload endpoints."""

    def __init__(self, app, max_requests: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit upload endpoints
        if request.url.path.startswith("/api/upload"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            # Periodically evict stale IPs to prevent memory leak
            if now - self._last_cleanup > _RATE_LIMIT_CLEANUP_INTERVAL:
                stale = [
                    ip for ip, ts in self._hits.items()
                    if not ts or now - ts[-1] > self.window
                ]
                for ip in stale:
                    del self._hits[ip]
                self._last_cleanup = now
            # Prune old entries for this IP
            self._hits[client_ip] = [
                t for t in self._hits[client_ip] if now - t < self.window
            ]
            if len(self._hits[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                )
            self._hits[client_ip].append(now)
        return await call_next(request)


def _cleanup_old_jobs() -> int:
    """Remove job directories older than MAX_JOB_AGE_SECONDS."""
    removed = 0
    now = time.time()
    for base_dir in [settings.upload_dir, settings.output_dir]:
        base = Path(base_dir)
        if not base.exists():
            continue
        for job_dir in base.iterdir():
            if not job_dir.is_dir():
                continue
            age = now - job_dir.stat().st_mtime
            if age > MAX_JOB_AGE_SECONDS:
                shutil.rmtree(job_dir, ignore_errors=True)
                removed += 1
    return removed


@asynccontextmanager
async def lifespan(app: FastAPI):
    removed = _cleanup_old_jobs()
    if removed:
        logger.info("Cleaned up %d old job directories", removed)
    yield


app = FastAPI(
    title="RescueForge API",
    description="AI-powered fire department floor plan generator (FKS-compliant)",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────
_allowed_origins = [
    o.strip()
    for o in settings.cors_origins.split(",")
    if o.strip()
] or ["*"]

_use_credentials = "*" not in _allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_use_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Headers ───────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── Rate Limiting ───────────────────────────────────────────
app.add_middleware(RateLimitMiddleware, max_requests=20, window_seconds=60)

app.include_router(router, prefix="/api")
app.include_router(ws_router, prefix="/api")
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "rescueforge", "version": __version__}
