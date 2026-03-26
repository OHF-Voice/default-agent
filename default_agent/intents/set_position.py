from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class SetPositionHandler(IntentHandler):
    intent_type = "HassSetPosition"
    match_targets = True

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        position = int(handle_input.intent_result.entities["position"].value)

        await handle_input.hass.call_service(
            "cover",
            "set_cover_position",
            service_data={"position": position},
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
