from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class SetPositionHandler(IntentHandler):
    intent_type = "HassSetPosition"
    match_targets = True

    async def handle(self, input: HandleInput) -> HandleOutput:
        position = int(input.intent_result.entities["position"].value)

        await input.hass.call_service(
            "cover",
            "set_cover_position",
            service_data={"position": position},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)