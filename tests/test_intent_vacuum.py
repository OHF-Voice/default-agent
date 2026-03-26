"""Tests for HassVacuumStart intent handler."""

import pytest


@pytest.mark.asyncio
async def test_vacuum_start(async_converse, hass):
    """Test HassVacuumStart intent."""
    success, response = await async_converse("start smart vacuum")
    assert success, "Intent recognition failed"
    assert response == "Started"
    hass.call_service.assert_called_once_with(
        "vacuum",
        "start",
        service_data={"entity_id": "vacuum.current_vacuum"},
    )


@pytest.mark.asyncio
async def test_vacuum_return_to_base(async_converse, hass):
    """Test HassVacuumReturnToBase intent."""
    success, response = await async_converse("return smart vacuum to base")
    assert success, "Intent recognition failed"
    assert response == "Returning"
    hass.call_service.assert_called_once_with(
        "vacuum",
        "return_to_base",
        service_data={"entity_id": "vacuum.current_vacuum"},
    )


@pytest.mark.asyncio
async def test_vacuum_clean_area(async_converse, hass):
    """Test HassVacuumCleanArea intent."""
    success, response = await async_converse("clean in here")
    assert success, "Intent recognition failed"
    assert response == "Cleaning Current Area"
    hass.call_service.assert_called_once_with(
        "vacuum",
        "clean_area",
        service_data={
            "entity_id": "vacuum.current_vacuum",
            "cleaning_area_id": "current-area",
        },
    )
