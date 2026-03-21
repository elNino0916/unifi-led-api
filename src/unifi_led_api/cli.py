#!/usr/bin/env python3
"""
start.py
Entry CLI for the unofficial UniFi LED API.

Usage:
  unifi-led led on          # Turn LED(s) on
  unifi-led led off         # Turn LED(s) off
  unifi-led led on --dry-run  # Preview payload without sending
  unifi-led status          # Show current LED state per device
  unifi-led discover        # Auto-discover all UniFi devices and their IDs
  unifi-led fetch-config    # Auto-generate led_on.json / led_off.json

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

    load_dotenv(Path.cwd() / ".env")
except ImportError:
    pass

from aiohttp import web

from unifi_led_api import grab_token as token_mod
from unifi_led_api import led_logic
from unifi_led_api.app_config import AppConfig


def resolve_device_ids(base_dir: Path, config: AppConfig, group: str | None = None) -> list[str]:
    if not group:
        return config.device_ids

    groups_file = base_dir / "groups.json"
    if not groups_file.is_file():
        raise FileNotFoundError(f"Group '{group}' specified, but {groups_file.name} not found.")

    with groups_file.open("r", encoding="utf-8") as f:
        try:
            groups = json.load(f)
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to parse {groups_file.name}. Ensure it is valid.") from err

    if group not in groups:
        raise KeyError(f"Group '{group}' not found in {groups_file.name}.")

    if not isinstance(groups[group], list):
        raise ValueError(f"Group '{group}' must be a list of device IDs.")

    return groups[group]


async def process_device(
    session,
    config,
    base_dir,
    device_id,
    command,
    target_state=None,
    dry_run=False,
    color=None,
    brightness=None,
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

        if "led_override" not in dev_cfg:
            logging.warning(
                "Device '%s' lacks native LED override explicitly. "
                "Skipping to prevent Gateway/Switch corruption.",
                dev_cfg.get("name", device_id)
            )
            return

        on_payload, off_payload = led_logic.generate_led_payloads(
            dev_cfg, base_dir, device_id, write_files=True, color=color, brightness=brightness
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


async def handle_led_webhook(request):
    state = request.match_info.get("state")
    if state not in ("on", "off"):
        return web.Response(status=400, text="Invalid state, must be 'on' or 'off'")

    config = request.app["config"]
    session = request.app["session"]
    base_dir = request.app["base_dir"]

    color = request.query.get("color")
    brightness_str = request.query.get("brightness")
    brightness = int(brightness_str) if brightness_str and brightness_str.isdigit() else None

    group = request.query.get("group")
    device_arg = request.query.get("device")

    try:
        if device_arg:
            device_ids = [d.strip() for d in device_arg.split(",") if d.strip()]
        else:
            device_ids = resolve_device_ids(base_dir, config, group)
    except Exception as e:
        return web.Response(status=400, text=str(e))

    if not device_ids:
        return web.json_response({"status": "error", "message": "No devices targeted."}, status=400)

    try:
        tasks = [
            process_device(
                session, config, base_dir, device_id, "led", state, False, color, brightness
            )
            for device_id in device_ids
        ]
        await asyncio.gather(*tasks)
        return web.json_response({"status": "success", "state": state, "devices": len(device_ids)})
    except Exception as e:
        logging.error("Webhook processing error: %s", e)
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def run_server(config, session, base_dir, port=8080):
    app = web.Application()
    app["config"] = config
    app["session"] = session
    app["base_dir"] = base_dir
    app.router.add_route("*", "/led/{state}", handle_led_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    logging.info("Starting webhook server on 0.0.0.0:%s", port)
    await site.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


async def async_main(args):
    """Main async entrypoint taking CLI args."""
    base_dir = Path.cwd()

    if args.command == "setup":
        from unifi_led_api import setup_cli
        await setup_cli.run_setup(base_dir)
        return

    config = AppConfig.load()

    try:
        session, csrf = await token_mod.get_session(config)
    except Exception as e:
        sys.exit(f"ERROR: Session creation failed - {e}")

    try:
        dry_run = getattr(args, "dry_run", False)
        target_state = getattr(args, "state", None)

        if args.command == "discover":
            logging.info(
                "Discovering devices on controller %s (site: %s)",
                config.controller,
                config.site
            )
            devices = await led_logic.discover_devices(
                session, config.controller, config.site, timeout=config.timeout
            )
            print("\n" + "=" * 90)
            print(
                f"{'DEVICE NAME':<25} | {'MAC ADDRESS':<17} | "
                f"{'MODEL':<15} | {'TOGGLE':<6} | {'DEVICE ID'}"
            )
            print("-" * 90)
            for d in devices:
                name = d.get("name", d.get("mac", "Unknown"))
                mac = d.get("mac", "N/A")
                model = d.get("model", "N/A")
                dev_id = d.get("_id", "N/A")

                # Check for LED override compatibility
                has_toggle = "✅" if "led_override" in d else "❌"

                print(f"{name:<25} | {mac:<17} | {model:<15} |   {has_toggle}   | {dev_id}")
            print("=" * 90 + "\n")
            return

        if args.command == "serve":
            port = getattr(args, "port", 8080)
            await run_server(config, session, base_dir, port)
            return

        group = getattr(args, "group", None)
        device_arg = getattr(args, "device", None)

        try:
            if device_arg:
                device_ids = [d.strip() for d in device_arg.split(",") if d.strip()]
            else:
                device_ids = resolve_device_ids(base_dir, config, group)
        except Exception as e:
            sys.exit(f"ERROR: {e}")

        if not device_ids:
            sys.exit("ERROR: No devices configured. Use UNIFI_DEVICE_ID, --group, or --device.")

        color = getattr(args, "color", None)
        brightness = getattr(args, "brightness", None)
        tasks = [
            process_device(
                session,
                config,
                base_dir,
                device_id,
                args.command,
                target_state,
                dry_run,
                color,
                brightness,
            )
            for device_id in device_ids
        ]
        await asyncio.gather(*tasks)
    finally:
        await session.close()

    if args.command == "led":
        if dry_run:
            logging.info("Dry-run complete. No changes were made.")
        else:
            logging.info("Done. Set LED %s on %d device(s).", args.state, len(device_ids))
    elif args.command == "fetch-config":
        logging.info("Done. Generated config files for %d device(s).", len(device_ids))
        logging.info("Now run: python %s led on|off", sys.argv[0])
    elif args.command == "status":
        logging.info("Done. Queried %d device(s).", len(device_ids))


def main():
    parser = argparse.ArgumentParser(
        prog="start.py",
        description="Control UniFi Access Point LEDs via the internal REST API.",
        epilog="See .env.example for config. Full docs: https://github.com/elNino0916/unifi-led-api",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--group", help="Target a specific device group configured in groups.json")
    parser.add_argument(
        "--device", help="Target a specific device ID or comma-separated list of IDs"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # led on|off [--dry-run]
    led_parser = subparsers.add_parser("led", help="Turn device LED(s) on or off")
    led_parser.add_argument("state", choices=["on", "off"], help="Desired LED state")
    led_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the payload without sending it to the controller",
    )
    led_parser.add_argument("--color", help="Hex color code (e.g. '#0000ff') for supported APs")
    led_parser.add_argument(
        "--brightness",
        type=int,
        choices=range(0, 101),
        metavar="[0-100]",
        help="Brightness percentage 0-100 for supported APs",
    )

    # status
    subparsers.add_parser(
        "status",
        help="Show current LED override state for each device",
    )

    # discover
    subparsers.add_parser(
        "discover",
        help="Discover all devices connected to the UniFi controller and list their IDs",
    )

    # fetch-config
    subparsers.add_parser(
        "fetch-config",
        help="Fetch device config and generate JSON payloads",
    )

    # serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start a lightweight HTTP server to listen for webhooks (e.g., /led/on, /led/off)",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8080, help="Port to listen on (default: 8080)"
    )

    # setup
    subparsers.add_parser(
        "setup",
        help="Interactive setup wizard to configure .env and select devices",
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
