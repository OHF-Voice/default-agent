from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class ListAddItemHandler(IntentHandler):
    intent_type = "HassListAddItem"
    match_targets = True

    async def handle(self, input: HandleInput) -> HandleOutput:
        item = input.intent_result.entities["item"].value

        await input.hass.call_service(
            "todo",
            "add_item",
            service_data={"item": item},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)