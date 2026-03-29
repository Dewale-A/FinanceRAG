"""API Key authentication for FinanceRAG."""

import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify the API key from request header."""
    expected_key = os.getenv("API_KEY", "")
    if not expected_key:
        # If no API_KEY is set, skip auth (development mode)
        return None
    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )
    return api_key
