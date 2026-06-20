"""Dependency-injection entry points re-exported for routers."""
from app.core.config import Settings, get_settings
from app.core.redis import get_redis
from app.db.session import get_session as get_db
from app.shared.pagination import PaginationParams

__all__ = ["get_settings", "Settings", "get_redis", "get_db", "PaginationParams"]
