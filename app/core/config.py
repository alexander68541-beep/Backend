from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # App
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:3000"
    PUBLIC_PORTFOLIO_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Cloudinary (media uploads)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_UPLOAD_FOLDER: str = "folio"

    # Database
    DATABASE_URL: str = ""
    DB_SSL: bool = True

    # Username policy
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 30
    USERNAME_CHANGE_COOLDOWN_DAYS: int = 14

    # Rate limits
    RATE_LIMIT_USERNAME_CHECK: str = "30/minute"
    RATE_LIMIT_USERNAME_SET: str = "6/minute"
    RATE_LIMIT_DEFAULT_WRITE: str = "60/minute"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
