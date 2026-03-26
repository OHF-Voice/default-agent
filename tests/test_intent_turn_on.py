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
        target={"entity_id": ["light.current_light"]},
    )


@pytest.mark.asyncio
async def test_turn_on_lights_area(async_converse, hass):
    """Test HassTurnOn intent with lights in an area by name."""
    success, response = await async_converse("turn on the lights in the other area")
    assert success, "Intent recognition failed"
    assert response == "Turned on the lights"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_on",
        target={"entity_id": ["light.other_light"]},
    )


@pytest.mark.asyncio
async def test_turn_on_lights_floor(async_converse, hass):
    """Test HassTurnOn intent with lights in a floor by name."""
    success, response = await async_converse("turn on the lights on the first floor")
    assert success, "Intent recognition failed"
    assert response == "Turned on the lights"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_on",
        target={"entity_id": ["light.current_light", "light.other_light"]},
    )


@pytest.mark.asyncio
async def test_turn_on_name(async_converse, hass):
    """Test HassTurnOn intent with name."""
    success, response = await async_converse("turn on no area light")
    assert success, "Intent recognition failed"
    assert response == "Turned on the light"
    hass.call_service.assert_called_once_with(
        "light",
        "turn_on",
        target={"entity_id": ["light.no_area_light"]},
    )
