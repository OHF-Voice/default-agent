"""Tests for HassFanSetSpeed intent handler."""

import pytest


@pytest.mark.asyncio
async def test_fan_set_speed(async_converse, hass):
    """Test HassFanSetSpeed intent."""
    success, response = await async_converse("set fan speed to 50")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "fan",
        "set_percentage",
        service_data={"percentage": 50},
        target={"entity_id": ["fan.current_fan"]},
    )
