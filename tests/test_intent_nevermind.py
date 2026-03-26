"""Tests for HassNevermind intent handler."""

import pytest


@pytest.mark.asyncio
async def test_nevermind(async_converse):
    """Test HassNevermind intent."""
    success, response = await async_converse("nevermind")
    assert success, "Intent recognition failed"
    assert response == ""
