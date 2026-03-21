#!/usr/bin/env python3
"""
retry.py
Generic async retry helper for network operations.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


async def async_retry[T](
    coro_factory: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    delay: float = 1.0,
    description: str = "operation",
) -> T:
    """
    Retry an async operation up to *retries* times.

    *coro_factory* must be a zero-argument callable that returns a new
    awaitable on every call (e.g. a lambda or closure), because a coroutine
    object cannot be awaited twice.

    Raises the last exception if all attempts fail.
    """
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return await coro_factory()
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                logger.warning(
                    "%s try %d/%d failed, retrying in %.1fs... (%s)",
                    description,
                    attempt + 1,
                    retries,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("%s failed after %d attempts: %s", description, retries, e)
    raise last_error  # type: ignore[misc]
