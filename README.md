![Python](https://img.shields.io/badge/python-gray?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/docker-gray?style=for-the-badge&logo=docker)
![UniFi OS](https://img.shields.io/badge/OS%20Version-Tested%20with%205.1.5-darkgreen?style=for-the-badge&logo=ubiquiti)
![UniFi Network](https://img.shields.io/badge/Network%20Version-Tested%20with%2010.2.97-darkblue?style=for-the-badge&logo=ubiquiti)


<img width="1251" height="280" alt="image" src="https://github.com/user-attachments/assets/f3e6195e-68bc-4bc2-901a-490e40738ca6" />


Control UniFi Access Point LEDs via internal API — perfect for night mode scheduling and automation.

UniFi has never implemented a proper night mode scheduler for Access Points — despite users requesting it for years.
This project fills that gap with a lightweight, reliable Python-based API that sends PUT requests to the internal REST API of the AP.
Tested on U7 Pro and U6+.

> [!NOTE]  
> U6 UniFi APs support LED override ON/OFF only.  
> Color and brightness overrides are ignored by firmware.
> Brightness is only available on U7 series, color only on older APs.

## Features

- Turn device LEDs on or off programmatically
- **Auto-Discovery** — finds all UniFi APs and checks LED toggle compatibility easily
- **Webhook API Server** — built-in HTTP server explicitly designed to integrate with Node-RED, Home Assistant, etc.
- **Device Groups** — create custom zones like `upstairs` or `downstairs` using `groups.json`
- **CLI Color & Brightness** — supported on some AP models via `--color` and `--brightness`
- **Auto-config** — device config is fetched live on every run, so payloads are never stale
- **Per-device payloads** — each AP gets its own config files (`led_on_{id}.json` / `led_off_{id}.json`)
- **Multiple device support** — control several APs with one command or webhook
- **LED status** — check the current LED state without making changes
- **Dry-run mode** — preview payloads before sending
- **Cross-platform config** — `.env` file works on Linux, macOS, and Windows
- Works with UniFi OS and legacy controllers
- Simple command-line interface with `--help` support
- Suitable for cron jobs, automation, and Docker
- Published Docker image on [GitHub Container Registry](https://ghcr.io/elnino0916/unifi-led-api:latest)

## Why this does NOT use SSH

Many existing UniFi LED control solutions rely on SSH access to the access point
and manual modification of LED-related settings or scripts.

⚠️ SSH-based approaches have been observed to cause firmware corruption and device instability,
sometimes requiring recovery via TFTP.

**UniFi access points are not designed for persistent or repeated SSH access.**
Running SSH-based automation can:

- Increase CPU and memory usage on the AP
- Interfere with UniFi's internal configuration management
- Cause device instability, reprovisioning loops, or unexpected reboots
- Break silently after firmware updates

This project avoids SSH entirely and instead uses the same internal REST API
mechanism the UniFi controller itself uses to manage device configuration.
As a result, it is significantly more stable, safer, and closer to how UniFi
intended devices to be managed. This makes it suitable for long-term automation, cron jobs, and unattended operation.

## Requirements

- Python 3.9+
- `aiohttp` library (installed automatically)
- A UniFi Controller with API access
- A local UniFi user account (no 2FA)

## Installation

### With PyPI (Recommended)

```bash
pip install unifi-led-api
```
This gives you access to the global `unifi-led` command.

### From Source / Development

1. Clone this repository:
   ```bash
   git clone https://github.com/elNino0916/unifi-led-api.git
   cd unifi-led-api
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### With Docker

```bash
docker pull ghcr.io/elnino0916/unifi-led-api:main
```

Or build locally:

```bash
docker build -t unifi-led-api .
```

## Configuration

1. Copy the example env file and fill in your values:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your controller IP, credentials, and device ID(s).

That's it — you're ready to go. The tool fetches your device config automatically on every run.

### Finding your device ID

Your device ID is in the UniFi controller URL when viewing a device:

```
https://<controller-ip>/network/default/devices/properties/device/<DEVICE_ID>/general
```

> [!TIP]
> If you enter a wrong device ID, the error message will list all available devices with their names and IDs.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `UNIFI_USER` | Yes | — | Local UniFi username (no 2FA) |
| `UNIFI_PASS` | Yes | — | UniFi password |
| `UNIFI_CONTROLLER` | Yes | — | Controller URL (e.g. `https://192.168.1.1`) |
| `UNIFI_DEVICE_ID` | Yes | — | Device ID (comma-separated for multiple) |
| `UNIFI_SITE` | No | `default` | UniFi site name |
| `UNIFI_VERIFY_SSL` | No | `false` | Set to `true` for valid SSL certs |
| `UNIFI_TIMEOUT` | No | `10` | HTTP request timeout in seconds |

### Targeting Devices and Groups

You can define devices in the `.env` file via a comma-separated list:

```env
UNIFI_DEVICE_ID=device_id_1,device_id_2,device_id_3
```

Each device gets its own per-device config files and all are updated in a single run.

**Using Device Groups:**
Create a `groups.json` file in the root directory (see `groups.json.example`) to group IDs by name:
```json
{
  "upstairs": ["device_id_1", "device_id_2"],
  "downstairs": ["device_id_3"]
}
```
You can then run commands targeting only that group by placing the global `--group` argument **before** the sub-command:
```bash
unifi-led --group upstairs led on
```

**Specific Device Overrides:**
Similarly, you can override the target device list entirely by passing the global `--device` argument **before** the sub-command:
```bash
unifi-led --device device_id_3 led off
```

## Usage

### Interactive Setup
The easiest way to configure the project is with the built-in interactive wizard. It will prompt for your credentials, discover all connected devices, and let you select which ones to control.
```bash
unifi-led setup
```

Once completed, a `.env` file will be generated automatically in your current directory.

### Commands Overview

```bash
unifi-led --help
unifi-led led --help
unifi-led status --help
unifi-led discover --help
unifi-led serve --help
unifi-led setup --help
unifi-led fetch-config --help
```

### Turn LED On

```bash
unifi-led led on
```

For older supported access points, you can also pass a hex color and brightness percentage:
```bash
unifi-led led on --color "#0000ff" --brightness 50
```

### Turn LED Off

```bash
unifi-led led off
```

> [!NOTE]
> Every `led on/off` command automatically fetches the latest device config before pushing.
> This means config files are always up-to-date — no manual regeneration needed after firmware updates or config changes.

### Preview payload (dry-run)

```bash
unifi-led led on --dry-run
```

Shows the JSON payload that would be sent, without actually making any changes. Useful for debugging and first-time verification.

### Auto-Discovery

```bash
unifi-led discover
```

Finds all devices connected to the UniFi controller and lists their names, MAC addresses, models, and **device IDs**. It also includes a compatibility check table to show you if your firmware natively supports LED toggling.

### Check LED status

```bash
unifi-led status
```

Displays the current `led_override` state for each targeted device. No changes are made.

### Webhook API Server

Start a lightweight HTTP server to listen for webhooks. This is perfect for integrating UniFi LEDs with Node-RED, Home Assistant, or other platforms without invoking the CLI every time.

```bash
unifi-led serve --port 8080
```

You can then control devices with HTTP `GET` or `POST` requests:
- Turns on LEDs for `.env` configured devices: `http://localhost:8080/led/on`
- Using query parameters for groups and overrides: `http://localhost:8080/led/off?group=upstairs` or `http://localhost:8080/led/on?device=id1,id2`
- Using color and brightness: `http://localhost:8080/led/on?color=%23ff0000&brightness=100`

### Preview config without changing LEDs

```bash
unifi-led fetch-config
```

This fetches the device config and generates the JSON payload files without making any changes. Useful for inspecting what will be sent.

### Cron Example

Turn off LEDs every night at 10 PM:

```bash
0 22 * * * cd /path/to/my/env_folder && unifi-led led off
```

Turn on LEDs every morning at 7 AM:

```bash
0 7 * * * cd /path/to/my/env_folder && unifi-led led on
```

> [!TIP]
> The `.env` file is loaded automatically — no extra setup needed in cron.

### Docker

```bash
# Turn LEDs off
docker run --rm --env-file .env ghcr.io/elnino0916/unifi-led-api:main led off

# Turn LEDs on
docker run --rm --env-file .env ghcr.io/elnino0916/unifi-led-api:main led on

# Check LED status
docker run --rm --env-file .env ghcr.io/elnino0916/unifi-led-api:main status

# Preview payload (dry-run)
docker run --rm --env-file .env ghcr.io/elnino0916/unifi-led-api:main led on --dry-run

# Preview config
docker run --rm --env-file .env -v $(pwd):/app ghcr.io/elnino0916/unifi-led-api:main fetch-config
```

Docker cron example:

```bash
0 22 * * * docker run --rm --env-file /path/to/.env ghcr.io/elnino0916/unifi-led-api:main led off
0 7  * * * docker run --rm --env-file /path/to/.env ghcr.io/elnino0916/unifi-led-api:main led on
```

### Docker Compose (automated scheduling)

A `docker-compose.yml` is included that uses [ofelia](https://github.com/mcuadros/ofelia) for cron-based scheduling:

```bash
docker compose up -d
```

By default, LEDs turn off at 22:00 and on at 07:00. Customize the schedules via environment variables:

```bash
CRON_LED_OFF="0 0 23 * * *" CRON_LED_ON="0 0 6 * * *" docker compose up -d
```

## LED Payload Files

Config files are generated per-device as `led_on_{device_id}.json` and `led_off_{device_id}.json`.

These are **auto-generated on every run** from your live device config. You generally don't need to touch them, but they're written to disk so you can inspect exactly what gets sent.

If customizing manually:

- `led_override`: `"on"` or `"off"`
- `led_override_color`: LED color in hex format (e.g., `"#0000ff"`) **(Only older APs)**
- `led_override_color_brightness`: Brightness percentage (e.g., `"100"`) **(Only on some newer APs if it even works in the first place.)**

> [!CAUTION]  
> Do NOT modify anything in the JSON files except the LED fields.  
> Changing other values can break your device configuration.

## Troubleshooting

### Authentication Issues

- Ensure you're using a **local** UniFi account, not a Ubiquiti cloud account
- The account should **not** have 2FA enabled
- Check that the controller URL is correct and accessible

### SSL Certificate Errors

If you're using a self-signed certificate, set `UNIFI_VERIFY_SSL=false`

### CSRF Token Errors

The API automatically handles CSRF tokens. If you encounter issues, ensure your controller is running a compatible version.

## License

This project is provided under the MIT License.

## Disclaimer

This project is an unofficial tool and is not affiliated with, endorsed by, or supported by Ubiquiti Inc. or any of its subsidiaries in any way.
This software interacts with internal and undocumented UniFi controller and access point APIs, which are subject to change without notice. As a result, functionality may break at any time due to firmware updates, controller updates, configuration changes, or other modifications made by Ubiquiti.
**Use this tool only if you understand what it does and have verified it in a safe or non-production environment first.**
If you are unsure whether this tool is appropriate for your setup, do **not** use it.
