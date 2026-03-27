"""Tests for HassPauseTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_pause_timer(async_converse, hass):
    """Test HassPauseTimer intent."""
    success, response = await async_converse("pause the timer")
    assert success, "Intent recognition failed"
    assert response == "Timer paused"
    hass.run_command.assert_called_once_with(
        "intent/pause_timer",
        {},
    )


@pytest.mark.asyncio
async def test_pause_timer_with_name(async_converse, hass):
    """Test HassPauseTimer intent with timer name."""
    success, response = await async_converse("pause my timer named cookies")
    assert success, "Intent recognition failed"
    assert response == "Timer paused"
    hass.run_command.assert_called_once_with(
        "intent/pause_timer",
        {"name": "cookies"},
    )


@pytest.mark.asyncio
async def test_pause_timer_with_start_time(async_converse, hass):
    """Test HassPauseTimer intent with start time."""
    success, response = await async_converse("pause the timer for 5 minutes")
    assert success, "Intent recognition failed"
    assert response == "Timer paused"
    hass.run_command.assert_called_once_with(
        "intent/pause_timer",
        {"start_minutes": 5},
    )


@pytest.mark.asyncio
async def test_pause_timer_with_start_hours(async_converse, hass):
    """Test HassPauseTimer intent with start hours."""
    success, response = await async_converse("pause the timer for 2 hours")
    assert success, "Intent recognition failed"
    assert response == "Timer paused"
    hass.run_command.assert_called_once_with(
        "intent/pause_timer",
        {"start_hours": 2},
    )
