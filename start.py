#!/usr/bin/env python3
"""
start.py
Entry CLI for the unofficial UniFi LED API.

Usage:
  python start.py led on          # Turn LED(s) on
  python start.py led off         # Turn LED(s) off
  python start.py led on --dry-run  # Preview payload without sending
  python start.py status          # Show current LED state per device
  python start.py fetch-config    # Auto-generate led_on.json / led_off.json

Supports multiple devices concurrently utilizing an async event loop.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Load .env natively
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import grab_token as token_mod
import led_logic
from app_config import AppConfig


async def process_device(
    session, config, base_dir, device_id, command, target_state=None, dry_run=False
):
    """Handle processing a single device concurrently."""
    if command == "led":
        logging.info(
            "Device: %s → LED %s%s", device_id, target_state, " (dry-run)" if dry_run else ""
        )
        dev_cfg = await led_logic.fetch_device_config(
            session,
            config.controller,
            config.site,
            device_id,
            timeout=config.timeout,
        )

        on_payload, off_payload = led_logic.generate_led_payloads(
            dev_cfg, base_dir, device_id, write_files=True
        )
        body = on_payload if target_state == "on" else off_payload

        if dry_run:
            logging.info("Dry-run payload for %s:\n%s", device_id, json.dumps(body, indent=2))
        else:
            await led_logic.push_led_payload(
                session,
                config.controller,
                config.site,
                device_id,
                body,
                timeout=config.timeout,
            )

    elif command == "fetch-config":
        logging.info("Fetching config for device: %s", device_id)
        dev_cfg = await led_logic.fetch_device_config(
            session,
            config.controller,
            config.site,
            device_id,
            timeout=config.timeout,
        )
        led_logic.generate_led_payloads(dev_cfg, base_dir, device_id, write_files=True)

    elif command == "status":
        dev_cfg = await led_logic.fetch_device_config(
            session,
            config.controller,
            config.site,
            device_id,
            timeout=config.timeout,
        )
        name = dev_cfg.get("name", "unnamed")
        status = led_logic.get_led_status(dev_cfg)
        logging.info("Device: %s (%s) — LED is %s", name, device_id, status)


async def async_main(args):
    """Main async entrypoint taking CLI args."""
    config = AppConfig.load()
    base_dir = Path(__file__).resolve().parent

    try:
        session, csrf = await token_mod.get_session(config)
    except Exception as e:
        sys.exit(f"ERROR: Session creation failed - {e}")

    try:
        dry_run = getattr(args, "dry_run", False)
        target_state = getattr(args, "state", None)
        tasks = [
            process_device(
                session, config, base_dir, device_id, args.command, target_state, dry_run
            )
            for device_id in config.device_ids
        ]
        await asyncio.gather(*tasks)
    finally:
        await session.close()

    if args.command == "led":
        if dry_run:
            logging.info("Dry-run complete. No changes were made.")
        else:
            logging.info("Done. Set LED %s on %d device(s).", args.state, len(config.device_ids))
    elif args.command == "fetch-config":
        logging.info("Done. Generated config files for %d device(s).", len(config.device_ids))
        logging.info("Now run: python %s led on|off", sys.argv[0])
    elif args.command == "status":
        logging.info("Done. Queried %d device(s).", len(config.device_ids))


def main():
    parser = argparse.ArgumentParser(
        prog="start.py",
        description="Control UniFi Access Point LEDs via the internal REST API.",
        epilog="See .env.example for config. Full docs: https://github.com/elNino0916/unifi-led-api",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # led on|off [--dry-run]
    led_parser = subparsers.add_parser("led", help="Turn device LED(s) on or off")
    led_parser.add_argument("state", choices=["on", "off"], help="Desired LED state")
    led_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the payload without sending it to the controller",
    )

    # status
    subparsers.add_parser(
        "status",
        help="Show current LED override state for each device",
    )

    # fetch-config
    subparsers.add_parser(
        "fetch-config",
        help="Fetch device config and generate JSON payloads",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Initialize async event loop
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
