from ..intent_handler import IntentHandler, HandleInput, HandleOutput
from enum import IntFlag


class ClimateEntityFeature(IntFlag):
    TARGET_TEMPERATURE = 1
    TARGET_TEMPERATURE_RANGE = 2
    TARGET_HUMIDITY = 4
    FAN_MODE = 8
    PRESET_MODE = 16
    SWING_MODE = 32
    TURN_OFF = 128
    TURN_ON = 256
    SWING_HORIZONTAL_MODE = 512


class SetTemperatureHandler(IntentHandler):
    intent_type = "HassClimateSetTemperature"
    match_targets = True
    inferred_domain = "climate"
    required_features = ClimateEntityFeature.TARGET_TEMPERATURE

    async def handle(self, input: HandleInput) -> HandleOutput:
        temperature = float(input.intent_result.entities["temperature"].value)

        await input.hass.call_service(
            "climate",
            "set_temperature",
            service_data={"temperature": temperature},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)
