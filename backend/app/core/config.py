import os
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "LoyaltyOS — Intelligent Loyalty & Ledger Management Platform"
    APP_SHORT_NAME: str = "LoyaltyOS"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configuration
    # Explicit allowed origins (no wildcard strings when credentials are enabled)
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    # Restricted origin regex for Vercel preview/production deployments
    ALLOW_ORIGIN_REGEX: Optional[str] = r"^https:\/\/.*\.vercel\.app$"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration (Supabase PostgreSQL prepared)
    DATABASE_URL: str = ""
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Supabase Configuration (Phase 2 Auth & DB)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_JWT_ALGORITHM: str = "HS256"

    # Firebase Configuration (Phase 2 Google Auth)
    FIREBASE_PROJECT_ID: str = "loyaltyos-2a2a0"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""

    # Initial Role Assignments by Email (Configurable RBAC Seeds)
    ADMIN_EMAILS: List[str] = ["admin@loyaltyos.internal", "manager@loyaltyos.internal"]
    OPERATOR_EMAILS: List[str] = ["operator@loyaltyos.internal", "warehouse@loyaltyos.internal"]
    ANALYST_EMAILS: List[str] = ["analyst@loyaltyos.internal"]

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
