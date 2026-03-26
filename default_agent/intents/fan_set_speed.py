from enum import IntFlag

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class FanEntityFeature(IntFlag):
    SET_SPEED = 1
    OSCILLATE = 2
    DIRECTION = 4
    PRESET_MODE = 8
    TURN_OFF = 16
    TURN_ON = 32


class FanSetSpeedHandler(IntentHandler):
    intent_type = "HassFanSetSpeed"
    match_targets = True
    inferred_domain = "fan"
    required_features = FanEntityFeature.SET_SPEED

    async def handle(self, input: HandleInput) -> HandleOutput:
        percentage = int(input.intent_result.entities["percentage"].value)

        await input.hass.call_service(
            "fan",
            "set_percentage",
            service_data={"percentage": percentage},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)
