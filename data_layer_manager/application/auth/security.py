from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from data_layer_manager.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate X-API-Key header against configured app.api_key."""
    settings = get_settings()
    if api_key == settings.app.api_key:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
