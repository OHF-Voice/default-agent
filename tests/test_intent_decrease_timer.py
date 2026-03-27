"""Tests for HassDecreaseTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_decrease_timer(async_converse, hass):
    """Test HassDecreaseTimer intent."""
    success, response = await async_converse("remove 5 minutes from the timer")
    assert success, "Intent recognition failed"
    assert response == "5 minutes removed from timer"
    hass.run_command.assert_called_once_with(
        "intent/decrease_timer",
        {"minutes": 5},
    )


@pytest.mark.asyncio
async def test_decrease_timer_with_name(async_converse, hass):
    """Test HassDecreaseTimer intent with timer name."""
    success, response = await async_converse(
        "take 10 minutes off my timer named cookies"
    )
    assert success, "Intent recognition failed"
    assert response == "10 minutes removed from timer named cookies"
    hass.run_command.assert_called_once_with(
        "intent/decrease_timer",
        {"name": "cookies", "minutes": 10},
    )


@pytest.mark.asyncio
async def test_decrease_timer_with_start_time(async_converse, hass):
    """Test HassDecreaseTimer intent with start time."""
    success, response = await async_converse(
        "remove 30 seconds from the timer for 5 minutes"
    )
    assert success, "Intent recognition failed"
    assert response == "30 seconds removed from timer"
    hass.run_command.assert_called_once_with(
        "intent/decrease_timer",
        {"start_minutes": 5, "seconds": 30},
    )


@pytest.mark.asyncio
async def test_decrease_timer_with_hours(async_converse, hass):
    """Test HassDecreaseTimer intent with hours."""
    success, response = await async_converse("decrease the timer by 1 hour")
    assert success, "Intent recognition failed"
    assert response == "1 hours removed from timer"
    hass.run_command.assert_called_once_with(
        "intent/decrease_timer",
        {"hours": 1},
    )


@pytest.mark.asyncio
async def test_decrease_timer_with_hours_minutes_seconds(async_converse, hass):
    """Test HassDecreaseTimer intent with hours, minutes, and seconds."""
    success, response = await async_converse(
        "take 1 hour 30 minutes and 45 seconds off the timer"
    )
    assert success, "Intent recognition failed"
    assert response == "1 hours, 30 minutes and 45 seconds removed from timer"
    hass.run_command.assert_called_once_with(
        "intent/decrease_timer",
        {"hours": 1, "minutes": 30, "seconds": 45},
    )
