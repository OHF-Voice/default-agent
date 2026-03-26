"""Tests for HassListAddItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_list_add_item(async_converse, hass):
    """Test HassListAddItem intent."""
    success, response = await async_converse("add clean the garage to my todo list")
    assert success, "Intent recognition failed"
    assert response == "Added clean the garage"
    hass.call_service.assert_called_once_with(
        "todo",
        "add_item",
        service_data={"item": "clean the garage"},
        target={"entity_id": ["todo.list"]},
    )
