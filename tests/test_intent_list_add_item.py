"""Tests for HassListAddItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_list_add_item(async_converse, hass):
    """Test HassListAddItem intent."""
    success, response = await async_converse("add milk to the list")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "todo",
        "add_item",
        service_data={"item": "milk"},
        target={"entity_id": []},
    )