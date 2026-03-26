"""Tests for HassSetVolume and HassSetVolumeRelative intent handlers."""

import pytest


@pytest.mark.asyncio
async def test_set_volume(async_converse, hass):
    """Test HassSetVolume intent."""
    success, response = await async_converse("set the volume to 25 percent")
    assert success, "Intent recognition failed"
    assert response == "Volume set"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.25},
        target={"entity_id": ["media_player.tv"]},
    )


@pytest.mark.asyncio
async def test_set_volume_relative_up(async_converse, hass):
    """Test HassSetVolumeRelative intent with up."""
    success, response = await async_converse("increase volume")
    assert success, "Intent recognition failed"
    assert response == "Volume set"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.6},  # up 10% from 50%
        target={"entity_id": "media_player.tv"},
    )


@pytest.mark.asyncio
async def test_set_volume_relative_down(async_converse, hass):
    """Test HassSetVolumeRelative intent with down."""
    success, response = await async_converse("decrease volume")
    assert success, "Intent recognition failed"
    assert response == "Volume set"
    hass.call_service.assert_called_once_with(
        "media_player",
        "volume_set",
        service_data={"volume_level": 0.4},  # down 10% from 50%
        target={"entity_id": "media_player.tv"},
    )
