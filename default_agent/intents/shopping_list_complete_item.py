from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class HassShoppingListCompleteItemHandler(IntentHandler):
    intent_type = "HassShoppingListCompleteItem"
    match_targets = False

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        item = handle_input.intent_result.entities["item"].value

        await handle_input.hass.call_service(
            "shopping_list",
            "complete_item",
            service_data={"name": item},
        )

        return HandleOutput(success=True)
