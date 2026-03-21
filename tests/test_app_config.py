import os

import pytest

from app_config import AppConfig


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove all UNIFI_ env vars before each test to avoid leaking, and ignore .env."""
    for key in list(os.environ):
        if key.startswith("UNIFI_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setitem(AppConfig.model_config, "env_file", None)


def set_required(monkeypatch):
    """Set the minimum required env vars."""
    monkeypatch.setenv("UNIFI_CONTROLLER", "https://192.168.1.1")
    monkeypatch.setenv("UNIFI_USER", "admin")
    monkeypatch.setenv("UNIFI_PASS", "secret")
    monkeypatch.setenv("UNIFI_DEVICE_ID", "abc123")


class TestAppConfigLoad:
    def test_loads_all_required(self, monkeypatch):
        set_required(monkeypatch)
        cfg = AppConfig.load(_env_file=None)

        assert cfg.controller == "https://192.168.1.1"
        assert cfg.user == "admin"
        assert cfg.password == "secret"
        assert cfg.device_ids == ["abc123"]

    def test_strips_trailing_slash(self, monkeypatch):
        set_required(monkeypatch)
        monkeypatch.setenv("UNIFI_CONTROLLER", "https://192.168.1.1/")
        cfg = AppConfig.load(_env_file=None)
        assert cfg.controller == "https://192.168.1.1"

    def test_defaults(self, monkeypatch):
        set_required(monkeypatch)
        cfg = AppConfig.load(_env_file=None)
        assert cfg.site == "default"
        assert cfg.verify_ssl is False
        assert cfg.timeout == 10

    def test_custom_site_and_ssl(self, monkeypatch):
        set_required(monkeypatch)
        monkeypatch.setenv("UNIFI_SITE", "mysite")
        monkeypatch.setenv("UNIFI_VERIFY_SSL", "true")
        cfg = AppConfig.load(_env_file=None)
        assert cfg.site == "mysite"
        assert cfg.verify_ssl is True

    def test_custom_timeout(self, monkeypatch):
        set_required(monkeypatch)
        monkeypatch.setenv("UNIFI_TIMEOUT", "30")
        cfg = AppConfig.load(_env_file=None)
        assert cfg.timeout == 30

    def test_invalid_timeout_exits(self, monkeypatch):
        set_required(monkeypatch)
        monkeypatch.setenv("UNIFI_TIMEOUT", "notanumber")
        with pytest.raises(SystemExit):
            AppConfig.load(_env_file=None)

    def test_multiple_device_ids(self, monkeypatch):
        set_required(monkeypatch)
        monkeypatch.setenv("UNIFI_DEVICE_ID", "id1, id2, id3")
        cfg = AppConfig.load(_env_file=None)
        assert cfg.device_ids == ["id1", "id2", "id3"]

    def test_missing_controller_exits(self, monkeypatch):
        monkeypatch.setenv("UNIFI_USER", "admin")
        monkeypatch.setenv("UNIFI_PASS", "secret")
        monkeypatch.setenv("UNIFI_DEVICE_ID", "abc")
        with pytest.raises(SystemExit):
            AppConfig.load(_env_file=None)

    def test_missing_user_exits(self, monkeypatch):
        monkeypatch.setenv("UNIFI_CONTROLLER", "https://1.2.3.4")
        monkeypatch.setenv("UNIFI_DEVICE_ID", "abc")
        with pytest.raises(SystemExit):
            AppConfig.load(_env_file=None)
