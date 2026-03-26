"""Tests for HassLightSet intent handler."""

import pytest

from default_agent.util import RGBColor

@pytest.mark.asyncio
async def test_light_set_brightness(async_converse, hass):
    """Test HassLightSet intent with brightness."""
    success, response = await async_converse("set brightness to 50")
    assert success, "Intent recognition failed"
    assert response == "Brightness set"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_on",
        service_data={"brightness_pct": 50},
        target={"entity_id": ["light.current_light"]},
    )


@pytest.mark.asyncio
async def test_light_set_color(async_converse, hass):
    """Test HassLightSet intent with color."""
    success, response = await async_converse("set lights to red")
    assert success, "Intent recognition failed"
    assert response == "Color set"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_on",
        service_data={"rgb_color": RGBColor(255, 0, 0)},
        target={"entity_id": ["light.current_light"]},
    )
