"""Tests for HassTurnOn intent handler."""

import pytest


@pytest.mark.asyncio
async def test_turn_on_lights_current_area(async_converse, hass):
    """Test HassTurnOn intent with lights in the current area."""
    success, response = await async_converse("turn on the lights")
    assert success, "Intent recognition failed"
    assert response == "Turned on the lights"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_on",
        target={"entity_id": ["light.light_current_area"]},
    )
