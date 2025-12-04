"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # NGRS API endpoints
    ngrs_clocking_url: str
    ngrs_api_key: str | None = None
    
    # Port configuration
    titus_api_port: int = 8087
    titus_ui_port: int = 8088
    
    # Scheduler settings
    poll_interval_seconds: int = 60
    
    # Timezone for date/time operations
    timezone: str = "Asia/Singapore"
    
    # Database configuration
    database_path: str = "sim_state.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Module-level singleton
settings = Settings()
