#!/usr/bin/env python3
"""
start.py
Entry CLI for your unofficial UniFi API bits.

Usage:
  python start.py led on
  python start.py led off

Reads:
  UNIFI_USER, UNIFI_PASS, UNIFI_CONTROLLER, UNIFI_VERIFY_SSL

Cron example:
  UNIFI_USER=apiuser UNIFI_PASS='secret' python3 /path/start.py led off
"""

import os
import sys
from pathlib import Path

import grab_token as token_mod  # careful with name clash if this file is named token.py
import led_logic

# If your file is called token.py, the import above must be:
#   import token as token_mod
# which we already did. Just make sure the filename is exactly token.py
# and it's in the same directory as start.py.

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "led" or sys.argv[2] not in ("on", "off"):
        print(f"Usage: {sys.argv[0]} led on|off")
        sys.exit(1)

    mode = sys.argv[2]   # "on" or "off"

    # Base directory so the script works from cron (no cwd assumptions)
    base_dir = Path(__file__).resolve().parent

    # Get an authenticated session + csrf
    session, token, csrf = token_mod.get_session()
    controller = os.environ.get("UNIFI_CONTROLLER")
    if not controller:
        print("ERROR: UNIFI_CONTROLLER must be set in the environment", file=sys.stderr)
        sys.exit(1)

    site = os.environ.get("UNIFI_SITE", "default")
    device_id = os.environ.get("UNIFI_DEVICE_ID")
    if not device_id:
        print("ERROR: UNIFI_DEVICE_ID must be set in the environment", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Mode: {mode}")
    print(f"[*] Controller: {controller}")
    print(f"[*] Site: {site}")
    print(f"[*] Device ID: {device_id}")

    # Load LED payload JSON
    body = led_logic.load_led_payload(mode, base_dir)

    # Push to device
    led_logic.push_led_payload(session, controller, site, device_id, body)

    print("[*] Done.")


if __name__ == "__main__":
    main()
