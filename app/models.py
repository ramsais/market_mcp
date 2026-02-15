"""Type-safe data models for MCP responses.

This module defines Pydantic models for all API responses,
ensuring type safety and automatic validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Stock symbol not found",
                "error_code": "SYMBOL_NOT_FOUND",
                "details": {"symbol": "INVALID"},
                "timestamp": "2026-02-16T10:30:00Z"
            }
        }
    )


class StockPriceData(BaseModel):
    """Individual stock price data."""

    symbol: str = Field(..., description="Stock ticker symbol")
    price: Optional[float] = Field(None, description="Current price")
    currency: str = Field(default="USD", description="Price currency")
    timestamp: Optional[int] = Field(None, description="Unix timestamp of price")
    company_name: Optional[str] = Field(None, description="Company name if resolved")

    # Additional price data
    high: Optional[float] = Field(None, description="Day high price")
    low: Optional[float] = Field(None, description="Day low price")
    open: Optional[float] = Field(None, description="Opening price")
    previous_close: Optional[float] = Field(None, description="Previous closing price")

    # Metadata
    source: str = Field(default="finnhub", description="Data source")
    error: Optional[str] = Field(None, description="Error message if price unavailable")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol."""
        if not v:
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()

    @property
    def has_error(self) -> bool:
        """Check if this response contains an error."""
        return self.error is not None

    @property
    def change(self) -> Optional[float]:
        """Calculate price change from previous close."""
        if self.price is not None and self.previous_close is not None:
            return self.price - self.previous_close
        return None

    @property
    def change_percent(self) -> Optional[float]:
        """Calculate percentage change from previous close."""
        if self.price is not None and self.previous_close is not None and self.previous_close != 0:
            return ((self.price - self.previous_close) / self.previous_close) * 100
        return None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "price": 255.79,
                "currency": "USD",
                "timestamp": 1771016400,
                "company_name": "Apple Inc.",
                "high": 262.23,
                "low": 255.45,
                "open": 262.02,
                "previous_close": 261.73,
                "source": "finnhub"
            }
        }
    )


class MultiStockResponse(BaseModel):
    """Response for multiple stock prices."""

    stocks: List[StockPriceData] = Field(..., description="List of stock price data")
    source: str = Field(default="finnhub", description="Data source")
    count: int = Field(..., description="Total number of stocks")
    successful: int = Field(..., description="Number of successful requests")
    failed: int = Field(..., description="Number of failed requests")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stocks": [
                    {"symbol": "AAPL", "price": 255.79, "currency": "USD"},
                    {"symbol": "GOOGL", "price": 142.50, "currency": "USD"}
                ],
                "source": "finnhub",
                "count": 2,
                "successful": 2,
                "failed": 0
            }
        }
    )


class CompanyInfo(BaseModel):
    """Company information from symbol lookup."""

    symbol: str = Field(..., description="Stock ticker symbol")
    description: Optional[str] = Field(None, description="Company name/description")
    type: Optional[str] = Field(None, description="Security type")
    display_symbol: Optional[str] = Field(None, description="Display symbol")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol."""
        if not v:
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "description": "Apple Inc.",
                "type": "Common Stock",
                "display_symbol": "AAPL"
            }
        }
    )


class CompanySearchResponse(BaseModel):
    """Response for company search."""

    results: List[CompanyInfo] = Field(..., description="List of matching companies")
    query: str = Field(..., description="Search query")
    count: int = Field(..., description="Number of results")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "symbol": "AAPL",
                        "description": "Apple Inc.",
                        "type": "Common Stock"
                    }
                ],
                "query": "Apple",
                "count": 1
            }
        }
    )


class PopularStock(BaseModel):
    """Popular stock information."""

    symbol: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Industry sector")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology"
            }
        }
    )


class MarketIndex(BaseModel):
    """Market index information."""

    symbol: str = Field(..., description="Index symbol")
    name: str = Field(..., description="Index name")
    description: str = Field(..., description="Index description")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "^GSPC",
                "name": "S&P 500",
                "description": "US large-cap index"
            }
        }
    )


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    """Individual service health."""

    name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service status")
    message: Optional[str] = Field(None, description="Status message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "finnhub",
                "status": "healthy",
                "message": "Connected",
                "response_time_ms": 123.45
            }
        }
    )


class HealthResponse(BaseModel):
    """Comprehensive health check response."""

    status: HealthStatus = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: Optional[float] = Field(None, description="Application uptime in seconds")
    services: List[ServiceHealth] = Field(default_factory=list, description="Individual service health")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2026-02-16T10:30:00Z",
                "version": "1.0.0",
                "uptime_seconds": 3600.0,
                "services": [
                    {
                        "name": "finnhub",
                        "status": "healthy",
                        "message": "Connected"
                    }
                ]
            }
        }
    )

