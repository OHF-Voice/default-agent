from ..const import ClimateEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class SetTemperatureHandler(IntentHandler):
    intent_type = "HassClimateSetTemperature"
    match_targets = True
    inferred_domain = "climate"
    required_features = ClimateEntityFeature.TARGET_TEMPERATURE

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        temperature = float(handle_input.intent_result.entities["temperature"].value)
        await handle_input.hass.call_service(
            "climate",
            "set_temperature",
            service_data={"temperature": temperature},
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
