"""Tests for HassListCompleteItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_list_complete_item(async_converse, hass):
    """Test HassListCompleteItem intent."""
    success, response = await async_converse(
        "check off clean the garage from my todo list"
    )
    assert success, "Intent recognition failed"
    assert response == "Checked off clean the garage"
    hass.call_service.assert_called_once_with(
        "todo",
        "update_item",
        service_data={"item": "clean the garage", "status": "completed"},
        target={"entity_id": ["todo.list"]},
    )
