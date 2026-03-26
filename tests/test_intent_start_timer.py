"""Tests for HassStartTimer intent handler."""

import pytest


@pytest.mark.asyncio
async def test_start_timer(async_converse, hass):
    """Test HassStartTimer intent."""
    success, response = await async_converse("start a timer")
    assert success, "Intent recognition failed"
    assert response == ""
