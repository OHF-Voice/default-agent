"""Tests for HassIncreaseTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_increase_timer(async_converse, hass):
    """Test HassIncreaseTimer intent."""
    success, response = await async_converse("add 5 minutes to the timer")
    assert success, "Intent recognition failed"
    assert response == "5 minutes added to timer"
    hass.run_command.assert_called_once_with(
        "intent/increase_timer",
        {"minutes": 5},
    )


@pytest.mark.asyncio
async def test_increase_timer_with_name(async_converse, hass):
    """Test HassIncreaseTimer intent with timer name."""
    success, response = await async_converse(
        "increase my timer named cookies by 10 minutes"
    )
    assert success, "Intent recognition failed"
    assert response == "10 minutes added to timer named cookies"
    hass.run_command.assert_called_once_with(
        "intent/increase_timer",
        {"name": "cookies", "minutes": 10},
    )


@pytest.mark.asyncio
async def test_increase_timer_with_start_time(async_converse, hass):
    """Test HassIncreaseTimer intent with start time."""
    success, response = await async_converse(
        "add 30 seconds to the timer for 5 minutes"
    )
    assert success, "Intent recognition failed"
    assert response == "30 seconds added to timer"
    hass.run_command.assert_called_once_with(
        "intent/increase_timer",
        {"start_minutes": 5, "seconds": 30},
    )


@pytest.mark.asyncio
async def test_increase_timer_with_hours(async_converse, hass):
    """Test HassIncreaseTimer intent with hours."""
    success, response = await async_converse("increase the timer by 1 hour")
    assert success, "Intent recognition failed"
    assert response == "1 hours added to timer"
    hass.run_command.assert_called_once_with(
        "intent/increase_timer",
        {"hours": 1},
    )


@pytest.mark.asyncio
async def test_increase_timer_with_hours_minutes_seconds(async_converse, hass):
    """Test HassIncreaseTimer intent with hours, minutes, and seconds."""
    success, response = await async_converse(
        "add 1 hour 30 minutes and 45 seconds to the timer"
    )
    assert success, "Intent recognition failed"
    assert response == "1 hours, 30 minutes and 45 seconds added to timer"
    hass.run_command.assert_called_once_with(
        "intent/increase_timer",
        {"hours": 1, "minutes": 30, "seconds": 45},
    )
