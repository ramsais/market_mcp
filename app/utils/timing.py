"""Timing decorator utilities.

Keeps timing lightweight and consistent across the codebase.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Callable, Any, TypeVar, Optional, cast

from .logger import get_logger, kv

F = TypeVar("F", bound=Callable[..., Any])


def timed(name: Optional[str] = None, *, log_args: bool = False) -> Callable[[F], F]:
    """Decorator to log execution time."""

    def decorator(fn: F) -> F:
        op_name = name or getattr(fn, "__qualname__", getattr(fn, "__name__", "<fn>"))
        log = get_logger(getattr(fn, "__module__", __name__))

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                fields = {"op": op_name, "elapsed_ms": round(elapsed_ms, 2)}
                if log_args:
                    fields["args"] = args
                    fields["kwargs"] = kwargs
                log.info("timing %s", kv(**fields))

        return cast(F, wrapper)

    return decorator

