from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class HassShoppingListCompleteItemHandler(IntentHandler):
    intent_type = "HassShoppingListCompleteItem"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        item = input.intent_result.entities["item"].value

        await input.hass.call_service(
            "shopping_list",
            "complete_item",
            service_data={"name": item},
        )

        return HandleOutput(success=True)