"""Optional API key authentication dependency."""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.config import LAPO_API_KEYS, API_AUTH_ENABLED

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(_api_key_header)) -> str | None:
    """FastAPI dependency that enforces X-API-Key when auth is enabled.

    When LAPO_API_KEYS is unset the API is open to all — no header required.
    When LAPO_API_KEYS contains at least one key, every request must supply a
    matching value in the X-API-Key header or receive a 401.
    """
    if not API_AUTH_ENABLED:
        return None
    if api_key and api_key in LAPO_API_KEYS:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key. Supply a valid key in the X-API-Key header.",
    )
