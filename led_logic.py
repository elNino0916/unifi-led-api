#!/usr/bin/env python3
"""
led_logic.py
LED-related operations for UniFi devices.

Exposes:
  load_led_payload(mode: str, base_dir: Path) -> dict
  push_led_payload(session, controller, site, device_id, body: dict)
"""

from pathlib import Path
import json
import requests


def load_led_payload(mode: str, base_dir: Path) -> dict:
    """
    Load LED payload from led_on.json or led_off.json in base_dir.

    mode: "on" or "off"
    """
    filename = "led_on.json" if mode == "on" else "led_off.json"
    path = base_dir / filename

    if not path.is_file():
        raise FileNotFoundError(f"LED payload file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        body = json.load(f)

    return body


def push_led_payload(
    session: requests.Session,
    controller: str,
    site: str,
    device_id: str,
    body: dict,
):
    """
    Send the provided body as the new device document.

    Assumes:
      - session already has auth + x-csrf-token in headers
      - body is a valid UniFi device payload
    """
    # Make sure the _id is correct
    body["_id"] = device_id

    url = f"{controller}/proxy/network/api/s/{site}/rest/device/{device_id}"
    r = session.put(url, json=body, timeout=10)

    print("PUT", url)
    print("Status:", r.status_code)
    print("Response:", r.text[:300])

    r.raise_for_status()
