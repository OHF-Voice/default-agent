"""Tests for HassMediaPlayerMute intent handler."""

import pytest


@pytest.mark.asyncio
async def test_media_player_mute(async_converse, hass):
    """Test HassMediaPlayerMute intent."""
    success, response = await async_converse("mute")
    assert success, "Intent recognition failed"
    assert response == "Muted"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_mute",
        service_data={"is_volume_muted": True},
        target={"entity_id": ["media_player.stereo"]},
    )


@pytest.mark.asyncio
async def test_media_player_unmute(async_converse, hass):
    """Test HassMediaPlayerUnmute intent."""
    success, response = await async_converse("unmute")
    assert success, "Intent recognition failed"
    assert response == "Unmuted"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_mute",
        service_data={"is_volume_muted": False},
        target={"entity_id": ["media_player.stereo"]},
    )
