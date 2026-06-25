"""Application configuration (Pydantic v2 settings)."""
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # App
    app_name: str = "logistics-platform"
    app_env: str = "local"            # local | staging | production
    app_debug: bool = True
    api_base_path: str = "/api/v1"
    log_level: str = "info"
    backend_port: int = 8000

    # Database (runtime app role; RLS-enforced)
    database_url: str = "postgresql+psycopg://app_user:change_me_app@localhost:5432/logistics"
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security primitives (token issuance/auth flows are Sprint 2)
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # Identity plane: BYPASSRLS role for auth/provisioning (falls back to database_url in dev)
    system_database_url: str | None = None

    # Refresh-token cookie transport
    refresh_cookie_name: str = "lp_refresh"
    cookie_secure: bool = False          # True in staging/production
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None
    cookie_path: str = "/api/v1/auth"

    # Single-use token lifecycles
    email_verification_ttl_hours: int = 48
    password_reset_ttl_minutes: int = 30

    # Provisioning gate — replaced by the Super Admin permission in S2-T5
    provisioning_api_key: str | None = None

    # RBAC
    rbac_cache_ttl_seconds: int = 300
    bootstrap_superadmin_email: str | None = None  # promoted to platform admin on startup if present

    # Audit
    audit_default_page_size: int = 50
    audit_max_page_size: int = 100
    audit_export_max_rows: int = 50_000
    audit_retention_days: int = 365

    # ---------------------------------------------------------------- Security (S2-T8)
    # Master toggles + tunables — every control below is configurable and safe-by-default.
    security_headers_enabled: bool = True
    security_hsts_enabled: bool = True               # only emitted over prod/HTTPS
    security_hsts_max_age: int = 63_072_000          # 2 years
    security_csp: str = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    security_referrer_policy: str = "no-referrer"
    security_permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    security_frame_options: str = "DENY"

    # Rate limiting (Redis fixed-window; fail-open if Redis is unavailable)
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_global_per_minute: int = 1000         # per client IP, all routes
    rate_limit_auth_per_minute: int = 30             # per client IP, auth-sensitive POSTs

    # Account lockout / login-abuse protection
    login_max_failures: int = 10                     # per account within the window -> lock
    login_failure_window_seconds: int = 900          # 15 min rolling window
    login_lockout_seconds: int = 900                 # lock duration once tripped
    login_ip_max_failures: int = 50                  # per IP within window (distributed attack)
    abuse_alert_threshold: int = 100                 # auth failures / rate-blocks per IP -> alert

    # Password policy (applied at register / provision / reset; strengthening only)
    password_min_length: int = 10
    password_max_length: int = 128
    password_min_char_classes: int = 3               # of {lower, upper, digit, symbol}
    password_block_common: bool = True

    # Sessions
    session_max_concurrent: int = 10                 # active refresh families per user; 0 = unlimited

    # CSRF (origin/referer verification on cookie-authenticated unsafe requests)
    csrf_protection_enabled: bool = True
    csrf_allowed_origins: list[str] = []             # empty -> cors_origins + frontend_base_url

    # Email links (delivery is stubbed in Sprint 2 — links are logged, not sent)
    # Email links
    frontend_base_url: str = "https://logistics-platforms-6qqf2wdsi-aparna3.vercel.app"

# CORS
    cors_origins: list[str] = [
    "http://localhost:3000",
    "https://logistics-platforms-6qqf2wdsi-aparna3.vercel.app",
    "https://logistics-platforms-3uv37pcus-aparna3.vercel.app",
]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def _enforce_deployment_security(self) -> "Settings":
        """Fail-fast on insecure production/staging configuration (S2-T9 hardening).

        In non-local environments a default/weak JWT secret is fatal (forgeable tokens), and the
        refresh-token cookie must carry the Secure flag. Local/test runs are unaffected.
        """
        if self.app_env in ("staging", "production"):
            if self.jwt_secret in ("", "change_me") or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be set to a strong value (>=32 chars) in staging/production"
                )
            # Secure cookies are mandatory outside local; force-on as defence in depth.
            self.cookie_secure = True
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
