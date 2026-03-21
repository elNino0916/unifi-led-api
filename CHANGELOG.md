# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] — Unreleased

### Added
- `status` subcommand — view current LED override state per device without making changes.
- `--dry-run` flag for the `led` command — preview the payload without sending it.
- `docker-compose.yml` example with cron-based scheduling for automated LED control.
- `UNIFI_TIMEOUT` environment variable to configure HTTP request timeout (default: 10s).
- Generic `retry.py` helper — replaces duplicated retry logic across modules.
- Test coverage reporting via `pytest-cov` in CI.
- New tests for `AppConfig.load()`, `async_retry`, `fetch_device_config`, and `push_led_payload`.
- `py.typed` marker for PEP 561 typing support.
- This `CHANGELOG.md`.

### Changed
- Renamed `config.py` → `app_config.py` to avoid shadowing the stdlib/third-party module name.
- `Dockerfile` now installs via `pyproject.toml` (`pip install .`) instead of `requirements.txt`.
- Bumped Ruff pre-commit hook from `v0.3.0` → `v0.15.6`.
- Version bumped to `0.2.0` in `pyproject.toml`.

### Fixed
- Removed unreachable dead code in `grab_token.py` (duplicate CSRF fetch after `except` block).
- Updated `README.md` requirements section (Python 3.9+, `aiohttp` — was incorrectly listing Python 3.6+ and `requests`).

### Notes
- **Session caching** across CLI invocations was considered but is unnecessary: the session is already shared across all devices within a single `asyncio.gather` run. Since the CLI is stateless (run-and-exit), cross-invocation caching would add complexity with minimal benefit.
