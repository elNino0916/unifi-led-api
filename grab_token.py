#!/usr/bin/env python3
"""
grab_token.py
Handles UniFi auth and CSRF retrieval.

Environment variables:
  UNIFI_USER        - UniFi username (local user, no 2FA)
  UNIFI_PASS        - UniFi password
  UNIFI_CONTROLLER  - Controller URL (e.g. https://192.168.178.1)
  UNIFI_VERIFY_SSL  - "true"/"false" (default: false)

Exposes:
  get_session() -> (session, token, csrf)
"""

import os
import sys
import requests
import urllib3


def _read_config():
    """Read controller config from environment at call time (not import time)."""
    controller = os.environ.get("UNIFI_CONTROLLER")
    if not controller:
        raise RuntimeError("UNIFI_CONTROLLER must be set in the environment")
    verify_ssl = os.environ.get("UNIFI_VERIFY_SSL", "false").lower() in ("1", "true", "yes")
    return controller, verify_ssl


def _login(session: requests.Session, controller: str, username: str, password: str):
    """
    Try to log in using the new and old UniFi login endpoints.
    Raise RuntimeError on failure with debug info included.
    """
    login_urls = [
        f"{controller}/api/auth/login",  # UniFi OS / newer
        f"{controller}/api/login",       # legacy
    ]

    payload = {
        "username": username,
        "password": password,
        "rememberMe": True,
    }

    last_error = None

    for url in login_urls:
        print(f"[*] Trying login URL: {url}")
        try:
            resp = session.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"[!] Exception during POST to {url}: {e}")
            last_error = e
            continue

        print(f"[*] Login response status: {resp.status_code}")
        if not resp.ok:
            print(f"[DEBUG] Login response body from {url}: {resp.text}")
        else:
            print(f"[*] Login OK via {url}")
            return resp

        last_error = resp.text

    raise RuntimeError(f"Login failed: {last_error}")


def _get_csrf(session: requests.Session, controller: str) -> str:
    """
    Fetch CSRF token via /proxy/network/api/self.
    """
    url = f"{controller}/proxy/network/api/self"
    print(f"[*] Fetching CSRF from: {url}")
    r = session.get(url, timeout=10)
    print(f"[*] CSRF fetch status: {r.status_code}")

    csrf = r.headers.get("x-csrf-token")
    if not csrf:
        print("[!] No x-csrf-token header found in response headers:")
        for k, v in r.headers.items():
            print(f"    {k}: {v}")
        raise RuntimeError("Could not obtain CSRF token from /proxy/network/api/self")

    return csrf


def get_session():
    """
    Create an authenticated session and return (session, token, csrf).

    Uses env vars:
      UNIFI_USER, UNIFI_PASS, UNIFI_CONTROLLER, UNIFI_VERIFY_SSL
    """
    controller, verify_ssl = _read_config()

    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    username = os.environ.get("UNIFI_USER")
    password = os.environ.get("UNIFI_PASS")

    if not username or not password:
        raise RuntimeError("UNIFI_USER and UNIFI_PASS must be set in the environment")

    print("=== UniFi grab_token.get_session ===")
    print(f"[*] Controller    : {controller}")
    print(f"[*] VERIFY_SSL    : {verify_ssl}")
    print(f"[*] Username      : {username}")

    session = requests.Session()
    session.verify = verify_ssl
    session.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    })

    try:
        _login(session, controller, username, password)
    except RuntimeError as e:
        print("[DEBUG] Failed login details:")
        print("  Controller:", controller)
        print("  Username  :", username)
        raise

    token = session.cookies.get("TOKEN")
    if not token:
        print("[!] No TOKEN cookie after login. Cookies we got:")
        print("    ", session.cookies.get_dict())
        raise RuntimeError("No TOKEN cookie received after login")

    print("[*] TOKEN cookie acquired.")

    csrf = _get_csrf(session, controller)
    print("[*] CSRF token acquired.")

    session.headers["x-csrf-token"] = csrf

    return session, token, csrf


def main():
    """CLI usage: just print TOKEN + CSRF for debugging."""
    try:
        session, token, csrf = get_session()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    controller, verify_ssl = _read_config()
    print("\n=== UniFi Session Info ===")
    print("Controller:", controller)
    print("VERIFY_SSL:", verify_ssl)
    print("TOKEN:", token)
    print("CSRF :", csrf)


if __name__ == "__main__":
    main()
