"""Tests for HassShoppingListAddItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_shopping_list_add_item(async_converse, hass):
    """Test HassShoppingListAddItem intent."""
    success, response = await async_converse("add milk to shopping list")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "shopping_list",
        "add_item",
        service_data={"name": "milk"},
    )
