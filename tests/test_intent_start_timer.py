"""Tests for HassStartTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_start_timer(async_converse, hass):
    """Test HassStartTimer intent."""
    success, response = await async_converse("start a timer for 5 minutes")
    assert success, "Intent recognition failed"
    assert response == "Timer set for 5 minutes"
    hass.run_command.assert_called_once_with(
        "intent/start_timer",
        {"minutes": 5},
    )


@pytest.mark.asyncio
async def test_start_timer_with_name(async_converse, hass):
    """Test HassStartTimer intent with timer name."""
    success, response = await async_converse(
        "start a timer for 10 minutes named cookies"
    )
    assert success, "Intent recognition failed"
    assert response == "Timer set for 10 minutes named cookies"
    hass.run_command.assert_called_once_with(
        "intent/start_timer",
        {"minutes": 10, "name": "cookies"},
    )


@pytest.mark.asyncio
async def test_start_timer_with_hours_and_minutes(async_converse, hass):
    """Test HassStartTimer intent with hours and minutes."""
    success, response = await async_converse("set a timer for 1 hour and 30 minutes")
    assert success, "Intent recognition failed"
    assert response == "Timer set for 1 hours and 30 minutes"
    hass.run_command.assert_called_once_with(
        "intent/start_timer",
        {"hours": 1, "minutes": 30},
    )


@pytest.mark.asyncio
async def test_start_timer_with_seconds(async_converse, hass):
    """Test HassStartTimer intent with seconds."""
    success, response = await async_converse("timer for 45 seconds")
    assert success, "Intent recognition failed"
    assert response == "Timer set for 45 seconds"
    hass.run_command.assert_called_once_with(
        "intent/start_timer",
        {"seconds": 45},
    )
