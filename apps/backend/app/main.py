import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings, validate_startup_security
from app.core.database import is_application_ready, set_application_ready, probe_schema_compatibility
from app.models.base import Base, engine
# Import models to ensure they register on Base.metadata
import app.models.user
import app.models.detection
from app.api.v1.auth import router as auth_router
from app.api.v1.detect import router as detect_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.preferences import router as preferences_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trasco")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastAPI application worker lifespan...")
    # 1. Startup Security Configuration Validation
    try:
        validate_startup_security(settings)
    except SystemExit as exc:
        logger.critical(f"Startup security validation rejected configuration: {exc}")
        raise RuntimeError(f"Startup security rejected: {exc}") from exc

    # 2. Schema Compatibility Verification (Read-Only; no DDL performed by worker)
    probe_res = probe_schema_compatibility(engine)
    if not probe_res.compatible:
        err_summary = probe_res.errors or probe_res.missing_tables or probe_res.missing_columns
        logger.critical(f"Database schema compatibility probe failed: {err_summary}")
        raise RuntimeError(f"Database schema compatibility probe failed: {err_summary}")

    set_application_ready(True)
    logger.info("Application readiness verified. Worker ready to serve traffic.")
    try:
        yield
    finally:
        set_application_ready(False)
        engine.dispose()
        logger.info("Application shutdown: readiness reset and connections disposed.")


class ReadinessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Always allow static liveness probe and API documentation
        if request.url.path in ["/health", "/docs", "/redoc", f"{settings.API_V1_STR}/openapi.json"]:
            return await call_next(request)

        # Fail-closed interception when application readiness has not been established
        if not is_application_ready():
            if request.url.path == "/health/ready":
                return JSONResponse(
                    status_code=503,
                    content={"status": "unready", "detail": "Startup security or schema validation incomplete."}
                )
            return JSONResponse(
                status_code=503,
                content={"error": "Service Unavailable", "detail": "Application startup unready."}
            )

        return await call_next(request)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="TRASCO AI-Powered Threat Detection & Intervention Engine API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware Registration Order:
# 1. ReadinessMiddleware (inner layer: evaluates readiness on business traffic)
app.add_middleware(ReadinessMiddleware)

# 2. CORSMiddleware (outermost layer: intercepts OPTIONS preflight directly and wraps outgoing 503s with CORS headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(detect_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(preferences_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "TRASCO Backend API",
        "version": "1.0.0",
        "ai_status": "CONFIGURED_UNVERIFIED" if settings.GEMINI_API_KEY else "HEURISTIC_MODE"
    }


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    if not is_application_ready():
        return JSONResponse(
            status_code=503,
            content={"status": "unready", "detail": "Application startup unready."}
        )
    return {
        "status": "ready",
        "service": "TRASCO Backend API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
