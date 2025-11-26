# UniFi LED API

An unofficial Python API to control LED status on UniFi devices (access points, switches, etc.) via undocumented REST APIs.

## Features

- Turn device LEDs on or off programmatically
- Works with UniFi OS and legacy controllers
- Simple command-line interface
- Configurable via environment variables
- Suitable for cron jobs and automation

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
   pip3 install requests
   ```

## Configuration

Instructions can be found in the [wiki](https://github.com/elNino0916/unifi-led-api/wiki/%5BSTEP-1%5D-Gather-required-strings-&-create-json-files).

## Usage

### Turn LED On

```bash
source set_env.sh
python3 start.py led on
```

### Turn LED Off

```bash
source set_env.sh
python3 start.py led off
```

### Inline Environment Variables

```bash
UNIFI_USER=USERNAME UNIFI_PASS='PASSWORD' UNIFI_CONTROLLER='https://192.168.1.1' UNIFI_DEVICE_ID='your_device_id' python start.py led off
```

### Cron Example

Turn off LEDs every night at 10 PM:

```bash
0 22 * * * . /path/to/set_env.sh && /usr/bin/python3 /path/to/start.py led off
```

Turn on LEDs every morning at 7 AM:

```bash
0 7 * * * . /path/to/set_env.sh && /usr/bin/python3 /path/to/start.py led on
```

## LED Payload Configuration

The `led_on.json` and `led_off.json` files contain the device configuration payloads. You **need to customize these files to match your device settings**:

- `led_override`: `"on"` or `"off"`
- `led_override_color`: LED color in hex format (e.g., `"#0000ff"`) **(Only older APs)**
- `led_override_color_brightness`: Brightness percentage (e.g., `"100"`) **(Only on some newer APs if it even works in the first place.)**
- **DO NOT CHANGE ANY OTHER SETTINGS UNLESS YOU KNOW WHAT YOU ARE DOING!**

## Troubleshooting

### Authentication Issues

- Ensure you're using a **local** UniFi account, not a Ubiquiti cloud account
- The account should **not** have 2FA enabled
- Check that the controller URL is correct and accessible

### SSL Certificate Errors

If you're using a self-signed certificate, set `UNIFI_VERIFY_SSL=false`

### CSRF Token Errors

The API automatically handles CSRF tokens. If you encounter issues, ensure your controller is running a compatible version.+

### Other errors / config changes

You have not updated your json files after a config change / update. Please check out [Step 1](https://github.com/elNino0916/unifi-led-api/wiki/%5BSTEP-1%5D-Gather-required-strings-&-create-json-files) to recreate the json files.

## License

This project is provided as-is for educational and personal use.

## Disclaimer

This is an unofficial API tool. Use at your own risk. Not affiliated with or endorsed by Ubiquiti Inc.
