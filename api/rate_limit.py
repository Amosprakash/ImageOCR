# api/rate_limit.py
"""
Rate limiting middleware for API endpoints.
"""
from fastapi import Request, HTTPException, status
from typing import Dict
import time
from collections import defaultdict
from utils.logger import log
import os

# Rate limit configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# In-memory storage for rate limiting (use Redis in production)
request_counts: Dict[str, list] = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"


async def rate_limit_middleware(request: Request):
    """
    Rate limiting middleware.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not RATE_LIMIT_ENABLED:
        return
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/"]:
        return
    
    client_ip = get_client_ip(request)
    current_time = time.time()
    
    # Clean old requests outside the window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        log.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )
    
    # Add current request
    request_counts[client_ip].append(current_time)


def get_rate_limit_status(client_ip: str) -> Dict[str, int]:
    """
    Get current rate limit status for a client.
    
    Args:
        client_ip: Client IP address
        
    Returns:
        dict: Rate limit status
    """
    current_time = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    remaining = max(0, RATE_LIMIT_REQUESTS - len(request_counts[client_ip]))
    
    return {
        "limit": RATE_LIMIT_REQUESTS,
        "remaining": remaining,
        "window_seconds": RATE_LIMIT_WINDOW,
        "requests_made": len(request_counts[client_ip])
    }
