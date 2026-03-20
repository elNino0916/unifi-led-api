#!/usr/bin/env python3
"""
grab_token.py
Handles UniFi auth and CSRF retrieval using aiohttp.
"""

import asyncio
import logging
import sys

import aiohttp

from config import AppConfig

logger = logging.getLogger(__name__)


async def _login(session: aiohttp.ClientSession, config: AppConfig):
    """Try to log in using the new and old UniFi login endpoints."""
    login_urls = [
        f"{config.controller}/api/auth/login",  # UniFi OS / newer
        f"{config.controller}/api/login",       # legacy
    ]

    payload = {
        "username": config.user,
        "password": config.password,
        "rememberMe": True,
    }

    last_error = None

    for url in login_urls:
        logger.debug("Trying login URL: %s", url)
        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                logger.debug("Login response status: %s", resp.status)
                if not resp.ok:
                    text = await resp.text()
                    logger.debug("Login response body from %s: %s", url, text)
                    last_error = text
                    continue
                else:
                    logger.info("Login OK via %s", url)
                    return resp
        except Exception as e:
            logger.debug("Exception during POST to %s: %s", url, e)
            last_error = str(e)
            continue

    raise RuntimeError(f"Login failed: {last_error}")


async def _get_csrf(session: aiohttp.ClientSession, config: AppConfig) -> str:
    """Fetch CSRF token via /proxy/network/api/self."""
    url = f"{config.controller}/proxy/network/api/self"
    logger.debug("Fetching CSRF from: %s", url)
    async with session.get(url, timeout=10) as r:
        logger.debug("CSRF fetch status: %s", r.status)

        csrf = r.headers.get("x-csrf-token")
        if not csrf:
            logger.warning("No x-csrf-token header found in response headers:")
            for k, v in r.headers.items():
                logger.debug("  %s: %s", k, v)
            raise RuntimeError("Could not obtain CSRF token from /proxy/network/api/self")

        return csrf


async def get_session(config: AppConfig) -> tuple[aiohttp.ClientSession, str]:
    """
    Create an authenticated session and return (session, csrf).
    """
    logger.debug("=== UniFi grab_token.get_session ===")
    logger.debug("Controller    : %s", config.controller)
    logger.debug("VERIFY_SSL    : %s", config.verify_ssl)
    logger.debug("Username      : %s", config.user)

    connector = aiohttp.TCPConnector(ssl=config.verify_ssl)

    # UniFi controllers are often accessed via raw IP addresses.
    # aiohttp's CookieJar ignores cookies from raw IP addresses by default.
    # We must pass unsafe=True to allow these cookies.
    cookie_jar = aiohttp.CookieJar(unsafe=True)

    session = aiohttp.ClientSession(
        connector=connector,
        cookie_jar=cookie_jar,
        headers={
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
    )

    try:
        # Simple retry loop for authentication
        for attempt in range(3):
            try:
                await _login(session, config)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning("Login try %d failed, retrying... (%s)", attempt + 1, e)
                await asyncio.sleep(1)

        # Check if the TOKEN cookie is natively in the jar
        has_token = any(cookie.key == "TOKEN" for cookie in session.cookie_jar)
        if not has_token:
            logger.warning("No TOKEN cookie after login! Cookies: %s", list(session.cookie_jar))
            raise RuntimeError("No TOKEN cookie received after login")

        logger.debug("TOKEN cookie acquired.")

        csrf = await _get_csrf(session, config)
        logger.debug("CSRF token acquired.")

        session.headers.update({"x-csrf-token": csrf})

        return session, csrf

    except Exception:
        logger.error("Failed session initialization details:")
        logger.error("  Controller: %s", config.controller)
        logger.error("  Username  : %s", config.user)
        await session.close()
        raise

    csrf = await _get_csrf(session, config)
    logger.debug("CSRF token acquired.")

    session.headers.update({"x-csrf-token": csrf})

    return session, csrf


async def async_main():
    """CLI usage: just print Session + CSRF for debugging."""
    config = AppConfig.load()
    try:
        session, csrf = await get_session(config)
        await session.close()
    except Exception as e:
        sys.exit(f"ERROR: {e}")

    print("\n=== UniFi Session Info ===")
    print(f"Controller: {config.controller}")
    print(f"VERIFY_SSL: {config.verify_ssl}")
    print(f"CSRF : {csrf}")


if __name__ == "__main__":
    asyncio.run(async_main())
