from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class HassShoppingListRemoveItemHandler(IntentHandler):
    intent_type = "HassShoppingListRemoveItem"
    match_targets = False

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        item = handle_input.intent_result.entities["item"].value

        await handle_input.hass.call_service(
            "shopping_list",
            "remove_item",
            service_data={"name": item},
        )

        return HandleOutput(success=True)
