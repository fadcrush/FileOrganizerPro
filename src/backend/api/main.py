"""FastAPI application for FileOrganizer Pro SaaS backend."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse

from src.backend.database import init_db
from src.backend.api.routes import auth_router, health_router, operations_router
from src.backend.api.routes import duplicates, files, reports, categories
from src.backend.api import websocket


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    # Startup
    print("🚀 Initializing FileOrganizer Pro SaaS API...")
    init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("🛑 Shutting down FileOrganizer Pro SaaS API")


# Create FastAPI app
app = FastAPI(
    title="FileOrganizer Pro API",
    description="Cloud-based file organization and duplicate detection API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Middleware configuration
# CORS - Allow requests from frontend
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZIP compression for responses
app.add_middleware(GZIPMiddleware, minimum_size=1000)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    # Log the error
    print(f"❌ Unexpected error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(operations_router)
app.include_router(duplicates.router)
app.include_router(files.router)
app.include_router(reports.router)
app.include_router(categories.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Welcome to FileOrganizer Pro API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
