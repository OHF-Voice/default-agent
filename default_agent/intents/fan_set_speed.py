from ..const import FanEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class FanSetSpeedHandler(IntentHandler):
    intent_type = "HassFanSetSpeed"
    match_targets = True
    inferred_domain = "fan"
    required_features = FanEntityFeature.SET_SPEED

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        percentage = int(handle_input.intent_result.entities["percentage"].value)

        await handle_input.hass.call_service(
            "fan",
            "set_percentage",
            service_data={"percentage": percentage},
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
