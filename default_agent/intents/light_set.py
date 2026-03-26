from ..intent_handler import HandleInput, HandleOutput, IntentHandler
from ..util import color_name_to_rgb


class LightSetHandler(IntentHandler):
    intent_type = "HassLightSet"
    match_targets = True
    inferred_domain = "light"

    # We don't have required_features here because of light groups.
    # If some or all of the lights in the group support color/brightness, it
    # doesn't mean the light group itself will have the supported feature(s).

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        brightness_value = handle_input.intent_result.entities.get("brightness")
        color_value = handle_input.intent_result.entities.get("color")
        temperature_value = handle_input.intent_result.entities.get("temperature")

        service_data: dict = {}
        if brightness_value:
            service_data["brightness_pct"] = int(brightness_value.value)

        if color_value:
            service_data["rgb_color"] = color_name_to_rgb(color_value.value)

        if temperature_value:
            service_data["color_temp_kelvin"] = int(temperature_value.value)

        await handle_input.hass.call_service(
            "light",
            "turn_on",
            service_data=service_data,
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
