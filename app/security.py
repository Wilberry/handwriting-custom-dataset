"""Authentication dependencies for the REST API and operator UI."""

import secrets
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials

from app.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
basic_auth = HTTPBasic(auto_error=False)


def _configuration_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


def require_api_key(
    request: Request,
    supplied_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require X-API-Key when configured and always require it in production."""
    if not settings.api_key:
        if settings.is_production:
            raise _configuration_error("API_KEY is required in production")
        request.state.actor = "development-api"
        return

    if not supplied_key or not secrets.compare_digest(supplied_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    request.state.actor = "api-key"


def require_admin(
    request: Request,
    credentials: HTTPBasicCredentials | None = Security(basic_auth),
    settings: Settings = Depends(get_settings),
) -> str:
    """Protect the operator UI with configurable HTTP Basic credentials."""
    configured = bool(settings.admin_username and settings.admin_password)
    partially_configured = bool(settings.admin_username) != bool(settings.admin_password)

    if partially_configured or (settings.is_production and not configured):
        raise _configuration_error("ADMIN_USERNAME and ADMIN_PASSWORD must both be configured")
    if not configured:
        request.state.actor = "development-admin"
        return "development"

    valid = bool(
        credentials
        and secrets.compare_digest(credentials.username, settings.admin_username or "")
        and secrets.compare_digest(credentials.password, settings.admin_password or "")
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    request.state.actor = f"admin:{credentials.username}"
    return credentials.username


def require_same_origin(request: Request) -> None:
    """Reject browser form submissions originating from another host."""
    origin = request.headers.get("Origin")
    if origin and urlparse(origin).netloc != request.headers.get("host"):
        raise HTTPException(status_code=403, detail="Cross-origin form submission rejected")
