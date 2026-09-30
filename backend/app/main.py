"""FastAPI entrypoint configuring security headers, rate limiting, CORS whitelist, and routers."""
from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import audit, auth, optimization, simulation, twin
from app.services.db_service import db_service


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database schema and seed the 10-node supply chain network on startup."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db_service.seed_initial_data(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Secure Supply Chain Digital Twin with MILP Optimization and Disruption Simulation",
    docs_url="/docs",
    lifespan=lifespan,
)

app.state.limiter = simulation.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Inject HSTS, X-Content-Type-Options, and X-Frame-Options security headers."""
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Return service health probe."""
    return {"status": "healthy", "service": settings.app_name}


app.include_router(auth.router)
app.include_router(twin.router)
app.include_router(simulation.router)
app.include_router(optimization.router)
app.include_router(audit.router)
