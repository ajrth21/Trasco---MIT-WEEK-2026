import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
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
    # Initialize DB tables
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="TRASCO AI-Powered Threat Detection & Intervention Engine API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
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
        "ai_status": "ONLINE" if settings.GEMINI_API_KEY else "HEURISTIC_MODE"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

