from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class ListCompleteItemHandler(IntentHandler):
    intent_type = "HassListCompleteItem"
    match_targets = True

    async def handle(self, input: HandleInput) -> HandleOutput:
        item = input.intent_result.entities["item"].value

        await input.hass.call_service(
            "todo",
            "update_item",
            service_data={"item": item, "status": "completed"},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)
