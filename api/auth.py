# api/auth.py
"""
API authentication and security middleware.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import os
from utils.logger import log

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Load API keys from environment
VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(",")) if os.getenv("API_KEYS") else set()

# Disable auth in testing mode
TESTING_MODE = os.getenv("TESTING", "false").lower() == "true"


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        str: Validated API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # Skip auth in testing mode
    if TESTING_MODE:
        return "test-key"
    
    # Skip auth if no API keys configured (development mode)
    if not VALID_API_KEYS:
        log.warning("No API keys configured - authentication disabled")
        return "dev-mode"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in VALID_API_KEYS:
        log.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


def get_current_api_key(api_key: str = Security(verify_api_key)) -> str:
    """
    Dependency to get current validated API key.
    Use this in route dependencies.
    """
    return api_key
