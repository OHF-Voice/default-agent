"""Tests for HassShoppingListCompleteItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_shopping_list_complete_item(async_converse, hass):
    """Test HassShoppingListCompleteItem intent."""
    success, response = await async_converse("mark milk as complete on shopping list")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "shopping_list",
        "complete_item",
        service_data={"name": "milk"},
    )
