"""Tests for HassSetTemperature intent handler."""

import pytest


@pytest.mark.asyncio
async def test_set_temperature(async_converse, hass):
    """Test HassClimateSetTemperature intent."""
    success, response = await async_converse("set temperature to 72")
    assert success, "Intent recognition failed"
    assert "Temperature set" in response
    assert "72" in response
    hass.call_service.assert_called_once_with(
        "climate",
        "set_temperature",
        service_data={"temperature": 72.0},
        target={"entity_id": ["climate.thermostat"]},
    )
