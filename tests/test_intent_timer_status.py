"""Tests for HassTimerStatus intent handler."""

import pytest


@pytest.mark.asyncio
async def test_timer_status(async_converse, hass):
    """Test HassTimerStatus intent."""
    # Set up the mock to return a proper coroutine that returns a dict
    hass.run_command.return_value = {"timers": []}

    success, response = await async_converse("timer status")
    assert success, "Intent recognition failed"
    assert response == "No timers."
    hass.handle_intent.assert_called_once_with(
        "HassTimerStatus",
        "en",
        data={},
        device_id=None,
        satellite_id=None,
    )
    hass.run_command.assert_called_once_with(
        "intent/timer_status",
        {},
    )


@pytest.mark.asyncio
async def test_timer_status_with_name(async_converse, hass):
    """Test HassTimerStatus intent with timer name."""
    hass.run_command.return_value = {"timers": []}

    success, response = await async_converse("cookies timer status")
    assert success, "Intent recognition failed"
    assert response == "No timers."
    hass.handle_intent.assert_called_once_with(
        "HassTimerStatus",
        "en",
        data={"name": "cookies"},
        device_id=None,
        satellite_id=None,
    )
    hass.run_command.assert_called_once_with(
        "intent/timer_status",
        {"name": "cookies"},
    )


@pytest.mark.asyncio
async def test_timer_status_with_start_time(async_converse, hass):
    """Test HassTimerStatus intent with start time."""
    hass.run_command.return_value = {"timers": []}

    success, response = await async_converse("5 minute timer status")
    assert success, "Intent recognition failed"
    assert response == "No timers."
    hass.handle_intent.assert_called_once_with(
        "HassTimerStatus",
        "en",
        data={"start_minutes": 5},
        device_id=None,
        satellite_id=None,
    )
    hass.run_command.assert_called_once_with(
        "intent/timer_status",
        {"start_minutes": 5},
    )


@pytest.mark.asyncio
async def test_timer_status_with_start_hours(async_converse, hass):
    """Test HassTimerStatus intent with start hours."""
    hass.run_command.return_value = {"timers": []}

    success, response = await async_converse("2 hour timer status")
    assert success, "Intent recognition failed"
    assert response == "No timers."
    hass.handle_intent.assert_called_once_with(
        "HassTimerStatus",
        "en",
        data={"start_hours": 2},
        device_id=None,
        satellite_id=None,
    )
    hass.run_command.assert_called_once_with(
        "intent/timer_status",
        {"start_hours": 2},
    )


@pytest.mark.asyncio
async def test_timer_status_left(async_converse, hass):
    """Test HassTimerStatus intent with 'time left' phrasing."""
    hass.run_command.return_value = {"timers": []}

    success, response = await async_converse("how much time is left on the timer")
    assert success, "Intent recognition failed"
    assert response == "No timers."
    hass.handle_intent.assert_called_once_with(
        "HassTimerStatus",
        "en",
        data={},
        device_id=None,
        satellite_id=None,
    )
    hass.run_command.assert_called_once_with(
        "intent/timer_status",
        {},
    )
