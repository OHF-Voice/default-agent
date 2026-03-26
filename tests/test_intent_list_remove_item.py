"""Tests for HassListRemoveItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_list_remove_item(async_converse, hass):
    """Test HassListRemoveItem intent."""
    success, response = await async_converse(
        "remove clean the garage from my todo list"
    )
    assert success, "Intent recognition failed"
    assert response == "Removed clean the garage"
    hass.call_service.assert_called_once_with(
        "todo",
        "remove_item",
        service_data={"item": "clean the garage"},
        target={"entity_id": ["todo.list"]},
    )
