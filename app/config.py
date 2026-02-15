"""Configuration management using Pydantic Settings.

This module provides type-safe configuration with validation at startup.
Environment variables are loaded and validated using Pydantic.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation.

    All settings can be configured via environment variables or .env file.
    """

    # Finnhub API Configuration
    finnhub_api_key: str = Field(
        ...,
        description="Finnhub API key for stock market data",
        min_length=1
    )

    # Server Configuration
    mcp_port: int = Field(
        default=9001,
        description="Port for HTTP REST API server",
        ge=1024,
        le=65535
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # API Configuration
    api_timeout: int = Field(
        default=30,
        description="API request timeout in seconds",
        ge=1,
        le=300
    )

    api_rate_limit: int = Field(
        default=60,
        description="Maximum API calls per minute",
        ge=1
    )

    # Cache Configuration
    enable_cache: bool = Field(
        default=True,
        description="Enable response caching"
    )

    cache_ttl: int = Field(
        default=300,
        description="Cache TTL in seconds (5 minutes default)",
        ge=0
    )

    # Application Metadata
    app_name: str = Field(
        default="Market Data Server",
        description="Application name for MCP server"
    )

    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )

    # Environment
    environment: str = Field(
        default="production",
        description="Environment name (development, staging, production)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        valid_envs = {"development", "staging", "production"}
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v_lower

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Validated application settings

    Raises:
        ValidationError: If settings validation fails
    """
    return Settings()


# Convenience function for getting settings
settings = get_settings()

