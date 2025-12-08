# api/server.py
"""
FastAPI server for ImageAI Document AI Platform.
Main application with middleware, CORS, and route registration.

This is the refactored version of app.py with updated imports.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from contextlib import asynccontextmanager
import time
import os
from dotenv import load_dotenv

from utils.logger import log
from api import ocr_routes, rag_routes, async_routes

# Load environment variables
load_dotenv()

# Set Google Vision credentials from environment variable (if needed)
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("ImageAI Document AI Platform starting")
    yield
    log.info("ImageAI Document AI Platform shutting down")


app = FastAPI(
    title="ImageAI Document AI Platform",
    description="Complete OCR, RAG, and Knowledge Graph platform for document processing with async task support",
    version="2.0.0",
    lifespan=lifespan
)


# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0].get("msg", "Invalid input")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": first_error},
    )


# Enable CORS - Configure allowed origins via environment variable
# For production, specify exact domains instead of "*"
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


# Logging middleware
@app.middleware("http")
async def middleware(request: Request, call_next):
    start = time.time()
    
    # Rate limiting
    from api.rate_limit import rate_limit_middleware
    try:
        await rate_limit_middleware(request)
    except Exception as e:
        return JSONResponse(
            status_code=getattr(e, 'status_code', 500),
            content={"detail": str(e.detail) if hasattr(e, 'detail') else str(e)}
        )
    
    try:
        body = await request.json()
    except Exception:
        body = None

    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Add rate limit headers
    from api.rate_limit import get_rate_limit_status, get_client_ip
    client_ip = get_client_ip(request)
    rate_status = get_rate_limit_status(client_ip)
    response.headers["X-RateLimit-Limit"] = str(rate_status["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_status["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_status["window_seconds"])
    
    process = (time.time() - start) * 1000
    log.info(
        f"{request.method} {request.url.path} | body:{body} | "
        f"statuscode:{response.status_code} | processtime:{process:.2f}ms"
    )
    return response


# Register routers
app.include_router(ocr_routes.router, prefix="/api", tags=["OCR"])
app.include_router(rag_routes.router, prefix="/api", tags=["RAG"])
app.include_router(async_routes.router, prefix="/api", tags=["Async Tasks"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ImageAI Document AI Platform",
        "version": "2.0.0",
        "description": "Complete OCR, RAG, and Knowledge Graph platform",
        "endpoints": {
            "ocr": "/api/ocr/*",
            "rag": "/api/rag/*",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ImageAI"}
