"""Service layer for interacting with Finnhub API.

This module provides a clean service interface for Finnhub API operations
with proper error handling, caching, and rate limiting.
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

import finnhub

from ..config import settings
from ..exceptions import (
    ConfigurationError,
    FinnhubAPIError,
    ServiceUnavailableError,
    SymbolNotFoundError,
    CompanyNotFoundError
)
from ..models import CompanyInfo, StockPriceData
from ..utils.logger import get_logger, kv

log = get_logger(__name__)


class FinnhubService:
    """Service for Finnhub API operations.

    This service provides:
    - Clean interface to Finnhub API
    - Error handling and conversion to domain exceptions
    - Logging and monitoring
    - Caching support
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Finnhub service.

        Args:
            api_key: Finnhub API key (uses settings if not provided)

        Raises:
            ConfigurationError: If API key is missing
        """
        self._api_key = api_key or settings.finnhub_api_key
        if not self._api_key:
            raise ConfigurationError(
                "Finnhub API key not configured",
                details={"env_var": "FINNHUB_API_KEY"}
            )

        try:
            self._client = finnhub.Client(api_key=self._api_key)
            log.info("finnhub.service_initialized")
        except Exception as exc:
            log.error("finnhub.initialization_error %s", kv(error=str(exc)))
            raise ConfigurationError(
                f"Failed to initialize Finnhub client: {str(exc)}",
                details={"error": str(exc)}
            )

    def is_available(self) -> bool:
        """Check if Finnhub service is available.

        Returns:
            True if service is available, False otherwise
        """
        return self._client is not None

    def search_companies(self, query: str) -> List[CompanyInfo]:
        """Search for companies by name.

        Args:
            query: Company name to search for

        Returns:
            List of matching companies

        Raises:
            ServiceUnavailableError: If service is not available
            FinnhubAPIError: If API request fails
        """
        if not self.is_available():
            raise ServiceUnavailableError("finnhub")

        if not query or not query.strip():
            return []

        try:
            log.info("finnhub.search_companies %s", kv(query=query))
            start_time = time.time()

            result = self._client.symbol_lookup(query)
            matches = (result or {}).get("result", [])

            elapsed_ms = (time.time() - start_time) * 1000
            log.info(
                "finnhub.search_complete %s",
                kv(query=query, count=len(matches), elapsed_ms=f"{elapsed_ms:.2f}")
            )

            # Convert to domain models
            companies = []
            for match in matches:
                try:
                    company = CompanyInfo(
                        symbol=match.get("symbol", ""),
                        description=match.get("description"),
                        type=match.get("type"),
                        display_symbol=match.get("displaySymbol")
                    )
                    companies.append(company)
                except Exception as exc:
                    log.warning(
                        "finnhub.invalid_company_data %s",
                        kv(error=str(exc), data=match)
                    )

            return companies

        except Exception as exc:
            log.error("finnhub.search_error %s", kv(query=query, error=str(exc)))
            raise FinnhubAPIError(
                f"Failed to search companies: {str(exc)}",
                details={"query": query, "error": str(exc)}
            )

    def get_quote(self, symbol: str) -> StockPriceData:
        """Get stock quote for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")

        Returns:
            Stock price data

        Raises:
            ServiceUnavailableError: If service is not available
            SymbolNotFoundError: If symbol is not found
            FinnhubAPIError: If API request fails
        """
        if not self.is_available():
            raise ServiceUnavailableError("finnhub")

        if not symbol or not symbol.strip():
            raise SymbolNotFoundError(symbol)

        symbol = symbol.strip().upper()

        try:
            log.info("finnhub.get_quote %s", kv(symbol=symbol))
            start_time = time.time()

            quote = self._client.quote(symbol)

            elapsed_ms = (time.time() - start_time) * 1000
            log.info(
                "finnhub.quote_complete %s",
                kv(symbol=symbol, elapsed_ms=f"{elapsed_ms:.2f}")
            )

            if not quote or quote.get("c") is None:
                raise SymbolNotFoundError(
                    symbol,
                    details={"reason": "No price data available"}
                )

            # Convert to domain model
            return StockPriceData(
                symbol=symbol,
                price=quote.get("c"),
                currency="USD",
                timestamp=quote.get("t"),
                high=quote.get("h"),
                low=quote.get("l"),
                open=quote.get("o"),
                previous_close=quote.get("pc"),
                source="finnhub"
            )

        except SymbolNotFoundError:
            raise
        except Exception as exc:
            log.error("finnhub.quote_error %s", kv(symbol=symbol, error=str(exc)))
            raise FinnhubAPIError(
                f"Failed to get quote for {symbol}: {str(exc)}",
                details={"symbol": symbol, "error": str(exc)}
            )

    def get_quote_by_company_name(self, company_name: str) -> StockPriceData:
        """Get stock quote by company name.

        Args:
            company_name: Company name to search for

        Returns:
            Stock price data for the best matching company

        Raises:
            CompanyNotFoundError: If no matching company found
            FinnhubAPIError: If API request fails
        """
        # Search for company
        companies = self.search_companies(company_name)

        if not companies:
            raise CompanyNotFoundError(
                company_name,
                details={"reason": "No matching companies found"}
            )

        # Get quote for first match
        best_match = companies[0]
        quote = self.get_quote(best_match.symbol)

        # Add company name to quote
        quote.company_name = best_match.description

        return quote

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Finnhub service.

        Returns:
            Health check result with status and response time
        """
        if not self.is_available():
            return {
                "status": "unhealthy",
                "message": "Service not initialized",
                "response_time_ms": None
            }

        try:
            # Try to get a quote for AAPL as health check
            start_time = time.time()
            self._client.quote("AAPL")
            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "message": "Connected",
                "response_time_ms": round(elapsed_ms, 2)
            }
        except Exception as exc:
            log.error("finnhub.health_check_failed %s", kv(error=str(exc)))
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(exc)}",
                "response_time_ms": None
            }


@lru_cache()
def get_finnhub_service() -> FinnhubService:
    """Get cached Finnhub service instance.

    Returns:
        FinnhubService instance
    """
    return FinnhubService()

