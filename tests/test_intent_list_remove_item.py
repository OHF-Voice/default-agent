"""Tests for HassListRemoveItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_list_remove_item(async_converse, hass):
    """Test HassListRemoveItem intent."""
    success, response = await async_converse("remove milk from the list")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "todo",
        "remove_item",
        service_data={"item": "milk"},
        target={"entity_id": []},
    )