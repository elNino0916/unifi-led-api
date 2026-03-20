from pathlib import Path

import pytest
from led_logic import generate_led_payloads

@pytest.fixture
def sample_config():
    return {
        "_id": "690b5fe4a6d04a4269cf61c8",
        "name": "U7 Pro",
        "led_override": "off",
        "led_override_color": "#0000ff",
        "led_override_color_brightness": "100",
        "outdoor_mode_override": "off",
        "not_needed_field": "remove_this"
    }

def test_generate_led_payloads(tmp_path: Path, sample_config):
    device_id = sample_config["_id"]

    # Generate payloads without writing files
    on_payload, off_payload = generate_led_payloads(
        config=sample_config,
        base_dir=tmp_path,
        device_id=device_id,
        write_files=False
    )

    # Ensure they have the correct override state
    assert on_payload["led_override"] == "on"
    assert off_payload["led_override"] == "off"

    # Ensure standard fields were copied
    assert on_payload["name"] == "U7 Pro"
    assert off_payload["name"] == "U7 Pro"

    # Ensure unwanted fields are removed
    assert "not_needed_field" not in on_payload
    assert "not_needed_field" not in off_payload

    # Ensure it writes correctly when asked
    generate_led_payloads(
        config=sample_config,
        base_dir=tmp_path,
        device_id=device_id,
        write_files=True
    )

    assert (tmp_path / f"led_on_{device_id}.json").exists()
    assert (tmp_path / f"led_off_{device_id}.json").exists()
