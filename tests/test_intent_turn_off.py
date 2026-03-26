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
        target={"entity_id": ["light.current_light"]},
    )


@pytest.mark.asyncio
async def test_turn_off_lights_area(async_converse, hass):
    """Test HassTurnOff intent with lights in an area by name."""
    success, response = await async_converse("turn off the lights in the other area")
    assert success, "Intent recognition failed"
    assert response == "Turned off the lights"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_off",
        target={"entity_id": ["light.other_light"]},
    )


@pytest.mark.asyncio
async def test_turn_off_lights_floor(async_converse, hass):
    """Test HassTurnOff intent with lights in a floor by name."""
    success, response = await async_converse("turn off the lights on the first floor")
    assert success, "Intent recognition failed"
    assert response == "Turned off the lights"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_off",
        target={"entity_id": ["light.current_light", "light.other_light"]},
    )


@pytest.mark.asyncio
async def test_turn_off_name(async_converse, hass):
    """Test HassTurnOff intent with name."""
    success, response = await async_converse("turn off no area light")
    assert success, "Intent recognition failed"
    assert response == "Turned off the light"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_off",
        target={"entity_id": ["light.no_area_light"]},
    )
