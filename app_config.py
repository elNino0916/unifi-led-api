import os
import sys
from dataclasses import dataclass


@dataclass
class AppConfig:
    controller: str
    user: str
    password: str
    device_ids: list[str]
    site: str
    verify_ssl: bool
    timeout: int

    @classmethod
    def load(cls) -> "AppConfig":
        """Load and validate all necessary environment variables."""
        controller = os.environ.get("UNIFI_CONTROLLER")
        if not controller:
            sys.exit("ERROR: UNIFI_CONTROLLER must be set in the environment")

        user = os.environ.get("UNIFI_USER")
        password = os.environ.get("UNIFI_PASS")
        if not user or not password:
            sys.exit("ERROR: UNIFI_USER and UNIFI_PASS must be set in the environment")

        raw_ids = os.environ.get("UNIFI_DEVICE_ID", "")
        device_ids = [d.strip() for d in raw_ids.split(",") if d.strip()]
        if not device_ids:
            sys.exit("ERROR: UNIFI_DEVICE_ID must be set in the environment")

        site = os.environ.get("UNIFI_SITE", "default")
        verify_ssl = os.environ.get("UNIFI_VERIFY_SSL", "false").lower() in ("1", "true", "yes")

        try:
            timeout = int(os.environ.get("UNIFI_TIMEOUT", "10"))
        except ValueError:
            timeout = 10

        return cls(
            controller=controller.rstrip("/"),
            user=user,
            password=password,
            device_ids=device_ids,
            site=site,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )
