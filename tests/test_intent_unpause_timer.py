"""Tests for HassUnpauseTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_unpause_timer(async_converse, hass):
    """Test HassUnpauseTimer intent."""
    success, response = await async_converse("resume the timer")
    assert success, "Intent recognition failed"
    assert response == "Timer resumed"
    hass.run_command.assert_called_once_with(
        "intent/unpause_timer",
        {},
    )


@pytest.mark.asyncio
async def test_unpause_timer_with_name(async_converse, hass):
    """Test HassUnpauseTimer intent with timer name."""
    success, response = await async_converse("continue my timer named cookies")
    assert success, "Intent recognition failed"
    assert response == "Timer resumed"
    hass.run_command.assert_called_once_with(
        "intent/unpause_timer",
        {"name": "cookies"},
    )


@pytest.mark.asyncio
async def test_unpause_timer_with_start_time(async_converse, hass):
    """Test HassUnpauseTimer intent with start time."""
    success, response = await async_converse("resume the timer for 5 minutes")
    assert success, "Intent recognition failed"
    assert response == "Timer resumed"
    hass.run_command.assert_called_once_with(
        "intent/unpause_timer",
        {"start_minutes": 5},
    )


@pytest.mark.asyncio
async def test_unpause_timer_with_start_hours(async_converse, hass):
    """Test HassUnpauseTimer intent with start hours."""
    success, response = await async_converse("continue the timer for 2 hours")
    assert success, "Intent recognition failed"
    assert response == "Timer resumed"
    hass.run_command.assert_called_once_with(
        "intent/unpause_timer",
        {"start_hours": 2},
    )
