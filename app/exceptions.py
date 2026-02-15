"""Custom exceptions for MCP server.

This module defines custom exception classes for better error handling
and consistent error responses across the application.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base exception for all MCP-related errors.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ConfigurationError(MCPError):
    """Configuration-related errors (missing API keys, invalid settings, etc.)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class ValidationError(MCPError):
    """Input validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ExternalAPIError(MCPError):
    """External API errors (Finnhub, etc.)."""

    def __init__(
        self,
        message: str,
        service: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["service"] = service
        if status_code:
            details["status_code"] = status_code
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details=details
        )


class FinnhubAPIError(ExternalAPIError):
    """Specific error for Finnhub API issues."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            service="finnhub",
            status_code=status_code,
            details=details
        )


class ResourceNotFoundError(MCPError):
    """Resource not found errors."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["resource_type"] = resource_type
        details["resource_id"] = resource_id
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            details=details
        )


class SymbolNotFoundError(ResourceNotFoundError):
    """Stock symbol not found."""

    def __init__(self, symbol: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            resource_type="Stock Symbol",
            resource_id=symbol,
            details=details
        )


class CompanyNotFoundError(ResourceNotFoundError):
    """Company not found."""

    def __init__(self, company_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            resource_type="Company",
            resource_id=company_name,
            details=details
        )


class RateLimitError(MCPError):
    """Rate limit exceeded errors."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class CacheError(MCPError):
    """Cache-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details
        )


class ServiceUnavailableError(MCPError):
    """Service unavailable errors."""

    def __init__(
        self,
        service: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = message or f"{service} service is unavailable"
        details = details or {}
        details["service"] = service
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )

