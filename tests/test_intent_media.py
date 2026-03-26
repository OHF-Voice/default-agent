"""Tests for HassMediaPause intent handler."""

import pytest


@pytest.mark.asyncio
async def test_media_pause(async_converse, hass):
    """Test HassMediaPause intent."""
    success, response = await async_converse("pause TV")
    assert success, "Intent recognition failed"
    assert response == "Paused"
    hass.call_service.assert_called_once_with(
        "media_player",
        "media_pause",
        target={"entity_id": ["media_player.tv"]},
    )


@pytest.mark.asyncio
async def test_media_unpause(async_converse, hass):
    """Test HassMediaUnpause intent."""
    success, response = await async_converse("resume TV")
    assert success, "Intent recognition failed"
    assert response == "Resumed"
    hass.call_service.assert_called_once_with(
        "media_player",
        "media_play",
        target={"entity_id": ["media_player.tv"]},
    )


@pytest.mark.asyncio
async def test_media_next(async_converse, hass):
    """Test HassMediaNext intent."""
    success, response = await async_converse("next track")
    assert success, "Intent recognition failed"
    assert response == "Playing next"
    hass.call_service.assert_called_once_with(
        "media_player",
        "media_next_track",
        target={"entity_id": ["media_player.stereo"]},
    )


@pytest.mark.asyncio
async def test_media_previous(async_converse, hass):
    """Test HassMediaPrevious intent."""
    success, response = await async_converse("previous track")
    assert success, "Intent recognition failed"
    assert response == "Playing previous"
    hass.call_service.assert_called_once_with(
        "media_player",
        "media_previous_track",
        target={"entity_id": ["media_player.stereo"]},
    )
