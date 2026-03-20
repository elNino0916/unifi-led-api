#!/usr/bin/env python3
"""
led_logic.py
LED-related operations for UniFi devices via aiohttp.
"""

import asyncio
import copy
import json
import logging
from pathlib import Path

import aiohttp

logger = logging.getLogger(__name__)


def get_led_payload(mode: str, base_dir: Path, device_id: str) -> dict:
    """Legacy backward compatibility wrapper if file loads are strictly required."""
    path = base_dir / f"led_{mode}_{device_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path.name}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def push_led_payload(
    session: aiohttp.ClientSession,
    controller: str,
    site: str,
    device_id: str,
    body: dict,
):
    """Send the provided body as the new device document async."""
    body["_id"] = device_id
    url = f"{controller}/proxy/network/api/s/{site}/rest/device/{device_id}"

    for attempt in range(3):
        try:
            async with session.put(url, json=body, timeout=10) as r:
                logger.debug("PUT %s", url)
                logger.debug("Status: %s", r.status)
                text = await r.text()
                logger.debug("Response: %s", text[:300])
                r.raise_for_status()
                return
        except Exception as e:
            if attempt == 2:
                raise
            logger.warning("PUT payload try %d failed, retrying... (%s)", attempt + 1, e)
            await asyncio.sleep(1)


async def fetch_device_config(
    session: aiohttp.ClientSession,
    controller: str,
    site: str,
    device_id: str,
) -> dict:
    """Fetch the current device configuration from the UniFi controller async."""
    url = f"{controller}/proxy/network/api/s/{site}/stat/device"

    for attempt in range(3):
        try:
            logger.debug("Fetching device list from: %s", url)
            async with session.get(url, timeout=10) as r:
                logger.debug("Fetch status: %s", r.status)
                r.raise_for_status()
                data = await r.json()
                break
        except Exception as e:
            if attempt == 2:
                raise
            logger.warning("GET device config try %d failed, retrying... (%s)", attempt + 1, e)
            await asyncio.sleep(1)

    devices = data.get("data", [])

    for device in devices:
        if device.get("_id") == device_id:
            logger.info("Found device: %s (%s)", device.get('name', 'unnamed'), device_id)
            return device

    available = ", ".join(f"{d.get('name','?')} ({d.get('_id','?')})" for d in devices)
    raise RuntimeError(
        f"No device found with ID '{device_id}'.\n"
        f"Available devices: {available}"
    )


def generate_led_payloads(
    config: dict, base_dir: Path, device_id: str, write_files: bool = True
) -> tuple[dict, dict]:
    """
    Generate per-device led_on and led_off dict payloads from a device config.
    If write_files is True, also saves them to led_on_{device_id}.json and led_off_{device_id}.json.
    Returns (on_payload, off_payload).
    """
    # Fields safe to include in the PUT payload
    KEEP_FIELDS = [
        "name", "snmp_contact", "snmp_location", "mgmt_network_id",
        "afc_enabled", "outdoor_mode_override",
        "led_override", "led_override_color", "led_override_color_brightness",
        "atf_enabled", "config_network", "mesh_sta_vap_enabled", "radio_table",
    ]

    payload = {}
    for key in KEEP_FIELDS:
        if key in config:
            payload[key] = copy.deepcopy(config[key])

    on_payload = copy.deepcopy(payload)
    on_payload["led_override"] = "on"

    off_payload = copy.deepcopy(payload)
    off_payload["led_override"] = "off"

    on_path = base_dir / f"led_on_{device_id}.json"
    off_path = base_dir / f"led_off_{device_id}.json"

    if write_files:
        for path, data in [(on_path, on_payload), (off_path, off_payload)]:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            logger.debug("Generated %s", path.name)

    return on_payload, off_payload
