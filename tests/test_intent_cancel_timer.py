"""Tests for HassCancelTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_cancel_timer(async_converse, hass):
    """Test HassCancelTimer intent."""
    success, response = await async_converse("cancel the timer")
    assert success, "Intent recognition failed"
    assert response == "Timer cancelled"
    hass.run_command.assert_called_once_with(
        "intent/cancel_timer",
        {},
    )


@pytest.mark.asyncio
async def test_cancel_timer_with_start_time(async_converse, hass):
    """Test HassCancelTimer intent with start time."""
    success, response = await async_converse("cancel the timer for 5 minutes")
    assert success, "Intent recognition failed"
    assert response == "Timer cancelled"
    hass.run_command.assert_called_once_with(
        "intent/cancel_timer",
        {"start_minutes": 5},
    )


@pytest.mark.asyncio
async def test_cancel_timer_with_start_hours(async_converse, hass):
    """Test HassCancelTimer intent with start hours."""
    success, response = await async_converse("cancel the timer for 2 hours")
    assert success, "Intent recognition failed"
    assert response == "Timer cancelled"
    hass.run_command.assert_called_once_with(
        "intent/cancel_timer",
        {"start_hours": 2},
    )
