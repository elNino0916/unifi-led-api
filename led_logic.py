#!/usr/bin/env python3
"""
led_logic.py
LED-related operations for UniFi devices.

Exposes:
  load_led_payload(mode: str, base_dir: Path) -> dict
  push_led_payload(session, controller, site, device_id, body: dict)
  fetch_device_config(session, controller, site, device_id) -> dict
  generate_led_files(config: dict, base_dir: Path)
"""

from pathlib import Path
import json
import copy
import requests


def load_led_payload(mode: str, base_dir: Path, device_id: str) -> dict:
    """
    Load LED payload from a device-specific or generic JSON file.

    Looks for led_{mode}_{device_id}.json first, then falls back to
    led_{mode}.json for backward compatibility.
    """
    device_file = base_dir / f"led_{mode}_{device_id}.json"
    generic_file = base_dir / f"led_{mode}.json"

    if device_file.is_file():
        path = device_file
    elif generic_file.is_file():
        path = generic_file
    else:
        raise FileNotFoundError(
            f"LED payload file not found for device {device_id}.\n"
            f"Run 'python start.py fetch-config' to generate config files automatically."
        )

    with path.open("r", encoding="utf-8") as f:
        body = json.load(f)

    print(f"[*] Loaded payload from {path.name}")
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
    body["_id"] = device_id

    url = f"{controller}/proxy/network/api/s/{site}/rest/device/{device_id}"
    r = session.put(url, json=body, timeout=10)

    print("PUT", url)
    print("Status:", r.status_code)
    print("Response:", r.text[:300])

    r.raise_for_status()


def fetch_device_config(
    session: requests.Session,
    controller: str,
    site: str,
    device_id: str,
) -> dict:
    """
    Fetch the current device configuration from the UniFi controller.
    Returns the device document as a dict.
    """
    url = f"{controller}/proxy/network/api/s/{site}/stat/device"
    print(f"[*] Fetching device list from: {url}")
    r = session.get(url, timeout=10)
    print(f"[*] Fetch status: {r.status_code}")
    r.raise_for_status()

    data = r.json()
    devices = data.get("data", [])

    for device in devices:
        if device.get("_id") == device_id:
            print(f"[*] Found device: {device.get('name', 'unnamed')} ({device_id})")
            return device

    available = ", ".join(f"{d.get('name','?')} ({d.get('_id','?')})" for d in devices)
    raise RuntimeError(
        f"No device found with ID '{device_id}'.\n"
        f"Available devices: {available}"
    )


def generate_led_files(config: dict, base_dir: Path, device_id: str):
    """
    Generate per-device led_on and led_off JSON files from a device config.
    Files are named led_on_{device_id}.json and led_off_{device_id}.json.
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

    for path, data in [(on_path, on_payload), (off_path, off_payload)]:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"[*] Generated {path.name}")

    return on_path, off_path
