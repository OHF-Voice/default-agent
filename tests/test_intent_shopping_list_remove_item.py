"""Tests for HassShoppingListRemoveItem intent handler."""

import pytest


@pytest.mark.asyncio
async def test_shopping_list_remove_item(async_converse, hass):
    """Test HassShoppingListRemoveItem intent."""
    success, response = await async_converse("remove milk from shopping list")
    assert success, "Intent recognition failed"
    hass.call_service.assert_called_once_with(
        "shopping_list",
        "remove_item",
        service_data={"name": "milk"},
    )