"""Tests for HassCancelAllTimers intent handler."""

import pytest


@pytest.mark.asyncio
async def test_cancel_all_timers(async_converse, hass):
    """Test HassCancelAllTimers intent."""
    # Set up the mock to return a proper coroutine that returns a dict
    hass.run_command.return_value = {"timer_ids": ["timer1"]}

    success, response = await async_converse("cancel all timers")
    assert success, "Intent recognition failed"
    assert response == "Canceled 1 timer."
    hass.run_command.assert_called_once_with(
        "intent/cancel_all_timers",
        {},
    )


@pytest.mark.asyncio
async def test_cancel_all_timers_with_area(async_converse, hass):
    """Test HassCancelAllTimers intent with area."""
    # Set up the mock to return a proper coroutine that returns a dict
    hass.run_command.return_value = {"timer_ids": ["timer1"]}

    success, response = await async_converse("cancel all timers in the Current Area")
    assert success, "Intent recognition failed"
    assert response == "Canceled 1 timer in Current Area."
    hass.run_command.assert_called_once_with(
        "intent/cancel_all_timers",
        {"area": "Current Area"},
    )
