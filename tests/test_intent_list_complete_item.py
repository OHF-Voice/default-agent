"""Tests for HassListCompleteItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_list_complete_item(async_converse, hass):
    """Test HassListCompleteItem intent."""
    success, response = await async_converse("mark milk as complete")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "todo",
        "update_item",
        service_data={"item": "milk", "status": "completed"},
        target={"entity_id": []},
    )