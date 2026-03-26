"""Tests for HassSetVolume intent handler."""

import pytest


@pytest.mark.asyncio
async def test_set_volume(async_converse, hass):
    """Test HassSetVolume intent."""
    success, response = await async_converse("set volume to 50")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.5},
        target={"entity_id": ["media_player.current_media_player"]},
    )
