from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class ListCompleteItemHandler(IntentHandler):
    intent_type = "HassListCompleteItem"
    match_targets = True

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        item = handle_input.intent_result.entities["item"].value

        await handle_input.hass.call_service(
            "todo",
            "update_item",
            service_data={"item": item, "status": "completed"},
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
