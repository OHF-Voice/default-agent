from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class ListRemoveItemHandler(IntentHandler):
    intent_type = "HassListRemoveItem"
    match_targets = True

    async def handle(self, input: HandleInput) -> HandleOutput:
        item = input.intent_result.entities["item"].value

        await input.hass.call_service(
            "todo",
            "remove_item",
            service_data={"item": item},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)
