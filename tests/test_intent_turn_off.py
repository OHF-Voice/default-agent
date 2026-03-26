"""Tests for HassTurnOff intent handler."""

import pytest


@pytest.mark.asyncio
async def test_turn_off_lights_current_area(async_converse, hass):
    """Test HassTurnOff intent with lights in the current area."""
    success, response = await async_converse("turn off the lights")
    assert success, "Intent recognition failed"
    assert response == "Turned off the lights"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_off",
        target={"entity_id": ["light.light_current_area"]},
    )
