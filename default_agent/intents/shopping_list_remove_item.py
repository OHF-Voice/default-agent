from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class HassShoppingListRemoveItemHandler(IntentHandler):
    intent_type = "HassShoppingListRemoveItem"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        item = input.intent_result.entities["item"].value

        await input.hass.call_service(
            "shopping_list",
            "remove_item",
            service_data={"name": item},
        )

        return HandleOutput(success=True)