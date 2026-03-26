from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class HassShoppingListAddItemHandler(IntentHandler):
    intent_type = "HassShoppingListAddItem"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        item = input.intent_result.entities["item"].value

        await input.hass.call_service(
            "shopping_list",
            "add_item",
            service_data={"name": item},
        )

        return HandleOutput(success=True)
