"""Tests for HassSetVolume intent handler."""

import pytest


@pytest.mark.asyncio
async def test_set_volume(async_converse, hass):
    """Test HassSetVolume intent."""
    success, response = await async_converse("set the volume to 50 percent")
    assert success, "Intent recognition failed"
    assert response == "Volume set"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.5},
        target={"entity_id": ["media_player.tv"]},
    )


@pytest.mark.asyncio
async def test_set_volume_relative_up(async_converse, hass):
    """Test HassSetVolumeRelative intent with up."""
    success, response = await async_converse("turn up the volume")
    assert success, "Intent recognition failed"
    assert response == "Volume set"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.6},
        target={"entity_id": "media_player.tv"},
    )


@pytest.mark.asyncio
async def test_set_volume_relative_down(async_converse, hass):
    """Test HassSetVolumeRelative intent with down."""
    success, response = await async_converse("turn down the volume")
    assert success, "Intent recognition failed"
    assert response == "Volume set"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.4},
        target={"entity_id": "media_player.tv"},
    )
