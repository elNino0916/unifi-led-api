![Python Version](https://img.shields.io/badge/python-gray?style=for-the-badge&logo=python)
![UniFi OS](https://img.shields.io/badge/OS%20Version-Tested%20with%205.0.12-darkgreen?style=for-the-badge&logo=ubiquiti)
![UniFi Network](https://img.shields.io/badge/Network%20Version-Tested%20with%2010.1.85-darkblue?style=for-the-badge&logo=ubiquiti)

> [!NOTE]  
> ## This project is maintained again as the official Home Assistant UniFi integration is way too buggy to get a working day/night mode.



<img width="1098" height="240" alt="image" src="https://github.com/user-attachments/assets/4092ad96-cd2e-487d-b0e2-1657f5e0462c" />

Control UniFi Access Point LEDs via internal API — perfect for night mode scheduling and automation.

UniFi has never implemented a proper night mode scheduler for Access Points — despite users requesting it for years.
This project fills that gap with a lightweight, reliable Python-based API that sends PUT requests to the internal REST API of the AP.
Tested on U7 Pro and U6+.
> [!NOTE]  
> Modern UniFi APs (U6/U7 series) support LED override ON/OFF only.  
> Color and brightness overrides are ignored by firmware.
## Features

- Turn device LEDs on or off programmatically
- **Auto-generate config** — `fetch-config` pulls your device settings automatically
- **Multiple device support** — control several APs with one command
- **Cross-platform config** — `.env` file works on Linux, macOS, and Windows
- Works with UniFi OS and legacy controllers
- Simple command-line interface with `--help` support
- Configurable via environment variables or `.env` file
- Suitable for cron jobs, automation, and Docker
- Docker-ready for NAS and server deployments

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

- Python 3.6+
- `requests` library
- A UniFi Controller with API access
- A local UniFi user account (no 2FA)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/elNino0916/unifi-led-api.git
   cd unifi-led-api
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Configuration

### Quick setup (recommended)

1. Copy the example env file and fill in your values:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your controller IP, credentials, and device ID(s).
3. Auto-generate the LED payload files:
   ```bash
   python3 start.py fetch-config
   ```
   This connects to your controller, pulls your device's current config, and generates `led_on.json` and `led_off.json` automatically.

That's it — you're ready to use the tool.

### Manual setup

Detailed manual instructions can be found in the [wiki](https://github.com/elNino0916/unifi-led-api/wiki/%5BSTEP-1%5D-Gather-required-strings-&-create-json-files).

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `UNIFI_USER` | Yes | — | Local UniFi username (no 2FA) |
| `UNIFI_PASS` | Yes | — | UniFi password |
| `UNIFI_CONTROLLER` | Yes | — | Controller URL (e.g. `https://192.168.1.1`) |
| `UNIFI_DEVICE_ID` | Yes | — | Device ID (comma-separated for multiple) |
| `UNIFI_SITE` | No | `default` | UniFi site name |
| `UNIFI_VERIFY_SSL` | No | `false` | Set to `true` for valid SSL certs |

Variables can be set via:
- A `.env` file in the project directory (recommended, cross-platform)
- Inline environment variables

### Multiple devices

Set `UNIFI_DEVICE_ID` to a comma-separated list:
```
UNIFI_DEVICE_ID=device_id_1,device_id_2,device_id_3
```

All devices will be updated in a single run.

## Usage

```
python3 start.py --help
python3 start.py led --help
python3 start.py fetch-config --help
```

### Auto-generate config files

```bash
python3 start.py fetch-config
```

### Turn LED On

```bash
python3 start.py led on
```

### Turn LED Off

```bash
python3 start.py led off
```

### Cron Example

Turn off LEDs every night at 10 PM:

```bash
0 22 * * * cd /path/to/unifi-led-api && /usr/bin/python3 start.py led off
```

Turn on LEDs every morning at 7 AM:

```bash
0 7 * * * cd /path/to/unifi-led-api && /usr/bin/python3 start.py led on
```

> [!TIP]
> The `.env` file is loaded automatically — no need to `source set_env.sh` in your cron jobs.

### Docker

Build and run:

```bash
docker build -t unifi-led-api .

# Turn LEDs off
docker run --env-file .env unifi-led-api led off

# Turn LEDs on
docker run --env-file .env unifi-led-api led on

# Auto-generate config (mount volume so JSON files persist)
docker run --env-file .env -v $(pwd):/app unifi-led-api fetch-config
```

For scheduled execution with Docker, use cron on the host:

```bash
0 22 * * * docker run --rm --env-file /path/to/.env -v /path/to/unifi-led-api:/app unifi-led-api led off
0 7  * * * docker run --rm --env-file /path/to/.env -v /path/to/unifi-led-api:/app unifi-led-api led on
```

## LED Payload Configuration

The `led_on.json` and `led_off.json` files contain the device configuration payloads.

**Recommended:** Run `python3 start.py fetch-config` to generate these automatically.

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

### Missing JSON files

Run `python3 start.py fetch-config` to auto-generate `led_on.json` and `led_off.json`.

### Other errors / config changes

You have not updated your json files after a config change / update. Run `python3 start.py fetch-config` to regenerate them, or check out [Step 1](https://github.com/elNino0916/unifi-led-api/wiki/%5BSTEP-1%5D-Gather-required-strings-&-create-json-files) to recreate the json files manually.

## License

This project is provided under the MIT License.

## Disclaimer

This project is an unofficial tool and is not affiliated with, endorsed by, or supported by Ubiquiti Inc. or any of its subsidiaries in any way.
This software interacts with internal and undocumented UniFi controller and access point APIs, which are subject to change without notice. As a result, functionality may break at any time due to firmware updates, controller updates, configuration changes, or other modifications made by Ubiquiti.
**Use this tool only if you understand what it does and have verified it in a safe or non-production environment first.**
If you are unsure whether this tool is appropriate for your setup, do **not** use it.
