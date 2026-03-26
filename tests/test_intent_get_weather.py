"""Tests for HassGetWeather intent handler."""

import pytest


@pytest.mark.asyncio
async def test_get_weather(async_converse, hass):
    """Test HassGetWeather intent."""
    success, response = await async_converse("what's the weather")
    assert success, "Intent recognition failed"
    assert response == ""
