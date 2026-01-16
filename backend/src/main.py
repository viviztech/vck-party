"""
VCK Platform - Main FastAPI Application
The main entry point for the VCK Political Party Management backend.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.redis import RedisClient
from src.core.exceptions import AppException

# Import routers
from src.auth.router import router as auth_router
from src.members.router import router as members_router
from src.hierarchy.router import router as hierarchy_router
from src.events.router import router as events_router
from src.voting.router import router as voting_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# Request Logging Middleware
# =============================================================================

async def request_logging_middleware(request: Request, call_next):
    """Log all incoming requests and their response times."""
    start_time = time.time()
    
    # Get client info
    client_host = request.client.host if request.client else "unknown"
    client_port = request.client.port if request.client else 0
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        # Log the exception
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"from {client_host}:{client_port} - {str(e)} "
            f"(took {process_time:.2f}s)"
        )
        raise
    
    # Calculate process time
    process_time = time.time() - start_time
    
    # Log successful requests
    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} "
        f"from {client_host}:{client_port} "
        f"(took {process_time:.2f}s)"
    )
    
    return response


# =============================================================================
# Rate Limiting Middleware
# =============================================================================

from src.core import redis


async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to requests."""
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Get client identifier (IP or user ID if authenticated)
    client_id = request.headers.get("x-forwarded-for", request.client.host)
    
    # Check rate limit
    is_allowed, remaining = await redis.check_rate_limit(
        key=f"api:{client_id}",
        limit=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests. Please try again later.",
                    "details": {"retry_after": 60}
                }
            },
            headers={"Retry-After": "60"}
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response


# =============================================================================
# Exception Handlers
# =============================================================================

# @app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


# @app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        }
    )


# =============================================================================
# Lifespan Context Manager
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application lifespan (startup and shutdown events)."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize database connections
        logger.info("Initializing database connections...")
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize Redis connection
        logger.info("Connecting to Redis...")
        await RedisClient.connect()
        logger.info("Redis connected successfully")
        
        logger.info("Application startup complete")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        
        # Close database connections
        logger.info("Closing database connections...")
        await close_db()
        
        # Disconnect Redis
        logger.info("Disconnecting from Redis...")
        await RedisClient.disconnect()
        
        logger.info("Application shutdown complete")


# =============================================================================
# Create FastAPI Application
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Political Party Management System API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request logging middleware (must be added after other middleware)
app.middleware("http")(request_logging_middleware)

# Rate limiting middleware (must be added after other middleware)
app.middleware("http")(rate_limit_middleware)


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the application and its dependencies.
    """
    from src.core.database import engine
    from src.core.redis import RedisClient
    
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "dependencies": {}
    }
    
    # Check database connection
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        await RedisClient.get_client().ping()
        health_status["dependencies"]["redis"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns basic API information.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_prefix": settings.API_V1_PREFIX,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# =============================================================================
# API Router Inclusion
# =============================================================================

# Include all module routers under the API v1 prefix
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(members_router, prefix=settings.API_V1_PREFIX)
app.include_router(hierarchy_router, prefix=settings.API_V1_PREFIX)
app.include_router(events_router, prefix=settings.API_V1_PREFIX)
app.include_router(voting_router, prefix=settings.API_V1_PREFIX)


# =============================================================================
# API Metadata
# =============================================================================

if settings.ENVIRONMENT == "development":
    # Add more detailed metadata in development
    app.description = """
    ## VCK Political Party Management System
    
    This is the backend API for the VCK Political Party Management system.
    
    ### Features:
    - **Authentication & Authorization**: JWT-based auth with RBAC
    - **Member Management**: Comprehensive member profiles and tracking
    - **Hierarchy Management**: District → Constituency → Ward → Booth structure
    - **Events & Campaigns**: Event management and campaign tracking
    - **Communications**: Announcements, forums, and messaging
    - **Voting**: eVoting system for elections
    - **Grievances**: Complaint management and resolution tracking
    - **Donations**: Donation collection and tracking
    
    ### Environment: Development
    """
