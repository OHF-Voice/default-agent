"""Tests for HassGetState intent handler."""

import pytest


@pytest.mark.asyncio
async def test_get_state_any(async_converse):
    """Test HassGetState intent."""
    success, response = await async_converse("are any lights on?")
    assert success, "Intent recognition failed"
    assert "Yes" in response
    assert "Current Light" in response
    assert "No Area Light" in response


@pytest.mark.asyncio
async def test_get_state_name(async_converse):
    """Test HassGetState intent."""
    success, response = await async_converse("is Current Light on?")
    assert success, "Intent recognition failed"
    assert "Yes" in response

    success, response = await async_converse("is Current Light off?")
    assert success, "Intent recognition failed"
    assert "No" in response

    success, response = await async_converse("is Other Light on?")
    assert success, "Intent recognition failed"
    assert "No" in response

    success, response = await async_converse("is Other Light off?")
    assert success, "Intent recognition failed"
    assert "Yes" in response
