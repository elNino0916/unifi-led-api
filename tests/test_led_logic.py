import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from unifi_led_api.led_logic import (
    fetch_device_config,
    generate_led_payloads,
    get_led_status,
    push_led_payload,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_config():
    return {
        "_id": "690b5fe4a6d04a4269cf61c8",
        "name": "U7 Pro",
        "led_override": "off",
        "led_override_color": "#0000ff",
        "led_override_color_brightness": "100",
        "outdoor_mode_override": "off",
        "not_needed_field": "remove_this",
    }


def _make_session_for_get(response_json, status=200):
    """Create a mock aiohttp session that returns *response_json* on GET."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=response_json)
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status}")

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=False)

    session = AsyncMock()
    session.get = MagicMock(return_value=ctx)
    return session


def _make_session_for_put(status=200):
    """Create a mock aiohttp session for PUT calls."""
    resp = AsyncMock()
    resp.status = status
    resp.text = AsyncMock(return_value='{"meta":{"rc":"ok"}}')
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status}")

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=False)

    session = AsyncMock()
    session.put = MagicMock(return_value=ctx)
    return session


# ---------------------------------------------------------------------------
# generate_led_payloads (pure logic — no mocks needed)
# ---------------------------------------------------------------------------


class TestGenerateLedPayloads:
    def test_correct_override_state(self, tmp_path: Path, sample_config):
        on_payload, off_payload = generate_led_payloads(
            config=sample_config,
            base_dir=tmp_path,
            device_id=sample_config["_id"],
            write_files=False,
        )
        assert on_payload["led_override"] == "on"
        assert off_payload["led_override"] == "off"

    def test_keeps_allowed_fields(self, tmp_path: Path, sample_config):
        on_p, _ = generate_led_payloads(
            config=sample_config,
            base_dir=tmp_path,
            device_id=sample_config["_id"],
            write_files=False,
        )
        assert on_p["name"] == "U7 Pro"
        assert on_p["outdoor_mode_override"] == "off"

    def test_strips_unknown_fields(self, tmp_path: Path, sample_config):
        on_p, off_p = generate_led_payloads(
            config=sample_config,
            base_dir=tmp_path,
            device_id=sample_config["_id"],
            write_files=False,
        )
        assert "not_needed_field" not in on_p
        assert "not_needed_field" not in off_p

    def test_writes_json_files(self, tmp_path: Path, sample_config):
        device_id = sample_config["_id"]
        generate_led_payloads(
            config=sample_config,
            base_dir=tmp_path,
            device_id=device_id,
            write_files=True,
        )
        on_file = tmp_path / f"led_on_{device_id}.json"
        off_file = tmp_path / f"led_off_{device_id}.json"

        assert on_file.exists()
        assert off_file.exists()

        on_data = json.loads(on_file.read_text())
        assert on_data["led_override"] == "on"


# ---------------------------------------------------------------------------
# get_led_status
# ---------------------------------------------------------------------------


class TestGetLedStatus:
    def test_returns_override_value(self):
        assert get_led_status({"led_override": "on"}) == "on"
        assert get_led_status({"led_override": "off"}) == "off"

    def test_returns_unknown_when_missing(self):
        assert get_led_status({}) == "unknown"


# ---------------------------------------------------------------------------
# fetch_device_config (async — mocked session)
# ---------------------------------------------------------------------------


class TestFetchDeviceConfig:
    async def test_returns_matching_device(self):
        data = {
            "data": [
                {"_id": "aaa", "name": "AP-1"},
                {"_id": "bbb", "name": "AP-2"},
            ]
        }
        session = _make_session_for_get(data)
        result = await fetch_device_config(session, "https://ctrl", "default", "bbb", timeout=5)
        assert result["name"] == "AP-2"

    async def test_raises_when_device_not_found(self):
        data = {"data": [{"_id": "aaa", "name": "AP-1"}]}
        session = _make_session_for_get(data)
        with pytest.raises(RuntimeError, match="No device found"):
            await fetch_device_config(session, "https://ctrl", "default", "zzz", timeout=5)


# ---------------------------------------------------------------------------
# push_led_payload (async — mocked session)
# ---------------------------------------------------------------------------


class TestPushLedPayload:
    async def test_sends_put_request(self):
        session = _make_session_for_put(200)
        body = {"led_override": "on", "name": "AP-1"}
        await push_led_payload(session, "https://ctrl", "default", "dev1", body, timeout=5)
        session.put.assert_called_once()

    async def test_sets_device_id_in_body(self):
        session = _make_session_for_put(200)
        body = {"led_override": "on"}
        await push_led_payload(session, "https://ctrl", "default", "dev1", body, timeout=5)
        assert body["_id"] == "dev1"
