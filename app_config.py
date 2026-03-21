import sys
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from typing import Any

class AppConfig(BaseSettings):
    controller: str = Field(..., alias="UNIFI_CONTROLLER")
    user: str = Field(..., alias="UNIFI_USER")
    password: str = Field(..., alias="UNIFI_PASS")
    device_ids: Any = Field(default=[], alias="UNIFI_DEVICE_ID")
    site: str = Field("default", alias="UNIFI_SITE")
    verify_ssl: bool = Field(False, alias="UNIFI_VERIFY_SSL")
    timeout: int = Field(10, alias="UNIFI_TIMEOUT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("device_ids", mode="before")
    @classmethod
    def parse_device_ids(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [d.strip() for d in v.split(",") if d.strip()]
        return v

    @field_validator("controller", mode="after")
    @classmethod
    def strip_controller_slash(cls, v: str) -> str:
        return v.strip().rstrip("/")
        
    @field_validator("user", "password", mode="after")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @classmethod
    def load(cls, **kwargs) -> "AppConfig":
        """Load and validate all necessary environment variables."""
        try:
            return cls(**kwargs)
        except ValidationError as e:
            sys.exit(f"ERROR: Configuration validation failed:\n{e}")
