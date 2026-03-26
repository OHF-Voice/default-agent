"""Tests for HassSetPosition intent handler."""

import pytest


@pytest.mark.asyncio
async def test_set_cover_position(async_converse, hass):
    """Test HassSetPosition intent."""
    success, response = await async_converse("set cover position to 50")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "cover",
        "set_cover_position",
        service_data={"position": 50},
        target={"entity_id": ["cover.current_cover"]},
    )