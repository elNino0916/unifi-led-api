#!/usr/bin/env python3
"""
start.py
Entry CLI for the unofficial UniFi LED API.

Usage:
  python start.py led on          # Turn LED(s) on
  python start.py led off         # Turn LED(s) off
  python start.py fetch-config    # Auto-generate led_on.json / led_off.json

Configuration is read from environment variables or a .env file in the
project directory. See .env.example for the full list of variables.

Supports multiple devices via comma-separated UNIFI_DEVICE_ID values.
"""

import argparse
import os
import sys
from pathlib import Path

# Load .env before anything reads env vars
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass  # python-dotenv is optional; env vars can be set manually

import grab_token as token_mod
import led_logic


def _get_env():
    """Read and validate required environment variables."""
    controller = os.environ.get("UNIFI_CONTROLLER")
    if not controller:
        print("ERROR: UNIFI_CONTROLLER must be set in the environment", file=sys.stderr)
        sys.exit(1)

    site = os.environ.get("UNIFI_SITE", "default")

    raw_ids = os.environ.get("UNIFI_DEVICE_ID", "")
    device_ids = [d.strip() for d in raw_ids.split(",") if d.strip()]
    if not device_ids:
        print("ERROR: UNIFI_DEVICE_ID must be set in the environment", file=sys.stderr)
        sys.exit(1)

    return controller, site, device_ids


def cmd_led(args):
    """Handle the 'led on/off' command."""
    base_dir = Path(__file__).resolve().parent
    controller, site, device_ids = _get_env()

    session, token, csrf = token_mod.get_session()

    for device_id in device_ids:
        print(f"\n[*] Device: {device_id} → LED {args.state}")
        config = led_logic.fetch_device_config(session, controller, site, device_id)
        led_logic.generate_led_files(config, base_dir, device_id)
        body = led_logic.load_led_payload(args.state, base_dir, device_id)
        led_logic.push_led_payload(session, controller, site, device_id, body)

    print(f"\n[*] Done. Set LED {args.state} on {len(device_ids)} device(s).")


def cmd_fetch_config(args):
    """Handle the 'fetch-config' command."""
    base_dir = Path(__file__).resolve().parent
    controller, site, device_ids = _get_env()

    session, token, csrf = token_mod.get_session()

    for device_id in device_ids:
        print(f"\n[*] Fetching config for device: {device_id}")
        config = led_logic.fetch_device_config(session, controller, site, device_id)
        led_logic.generate_led_files(config, base_dir, device_id)

    print(f"\n[*] Done. Generated config files for {len(device_ids)} device(s).")
    print(f"    Now run: python {sys.argv[0]} led on|off")


def main():
    parser = argparse.ArgumentParser(
        prog="start.py",
        description="Control UniFi Access Point LEDs via the internal REST API.",
        epilog="See .env.example for configuration. Full docs: https://github.com/elNino0916/unifi-led-api",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # led on|off
    led_parser = subparsers.add_parser("led", help="Turn device LED(s) on or off")
    led_parser.add_argument("state", choices=["on", "off"], help="Desired LED state")
    led_parser.set_defaults(func=cmd_led)

    # fetch-config
    fetch_parser = subparsers.add_parser(
        "fetch-config",
        help="Fetch device config and generate led_on.json / led_off.json",
    )
    fetch_parser.set_defaults(func=cmd_fetch_config)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
