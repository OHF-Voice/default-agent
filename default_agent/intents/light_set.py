from ..intent_handler import IntentHandler, HandleInput, HandleOutput
from ..util import color_name_to_rgb


class LightSetHandler(IntentHandler):
    intent_type = "HassLightSet"
    match_targets = True
    inferred_domain = "light"

    async def handle(self, input: HandleInput) -> HandleOutput:
        brightness_value = input.intent_result.entities.get("brightness")
        color_value = input.intent_result.entities.get("color")
        temperature_value = input.intent_result.entities.get("temperature")

        service_data: dict = {}
        if brightness_value:
            service_data["brightness_pct"] = int(brightness_value.value)

        if color_value:
            service_data["rgb_color"] = color_name_to_rgb(color_value.value)

        if temperature_value:
            service_data["color_temp_kelvin"] = int(temperature_value.value)

        await input.hass.call_service(
            "light",
            "turn_on",
            service_data=service_data,
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)