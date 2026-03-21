import pytest

from unifi_led_api.retry import async_retry


class TestAsyncRetry:
    async def test_succeeds_on_first_try(self):
        call_count = 0

        async def _op():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await async_retry(lambda: _op(), retries=3, delay=0, description="test")
        assert result == "ok"
        assert call_count == 1

    async def test_succeeds_after_retries(self):
        call_count = 0

        async def _op():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("not yet")
            return "recovered"

        result = await async_retry(lambda: _op(), retries=3, delay=0, description="test")
        assert result == "recovered"
        assert call_count == 3

    async def test_raises_after_exhausting_retries(self):
        async def _fail():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            await async_retry(lambda: _fail(), retries=2, delay=0, description="test")

    async def test_returns_correct_type(self):
        async def _op():
            return 42

        result = await async_retry(lambda: _op(), retries=1, delay=0, description="test")
        assert result == 42
        assert isinstance(result, int)
