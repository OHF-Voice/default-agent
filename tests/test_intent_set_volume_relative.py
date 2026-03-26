"""Tests for HassSetVolumeRelative intent handler."""

import pytest


@pytest.mark.asyncio
async def test_set_volume_relative_up(async_converse, hass):
    """Test HassSetVolumeRelative intent with up."""
    success, response = await async_converse("increase volume")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        target={"entity_id": "media_player.tv"},
    )


@pytest.mark.asyncio
async def test_set_volume_relative_down(async_converse, hass):
    """Test HassSetVolumeRelative intent with down."""
    success, response = await async_converse("decrease volume")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        target={"entity_id": "media_player.tv"},
    )
