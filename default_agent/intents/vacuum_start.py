from ..const import VacuumEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class VacuumStartHandler(IntentHandler):
    intent_type = "HassVacuumStart"
    match_targets = True
    inferred_domain = "vacuum"
    required_features = VacuumEntityFeature.START

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        if handle_input.target_entity_ids:
            entity_id = handle_input.target_entity_ids[0]
        else:
            entity_id = "all"

        await handle_input.hass.call_service(
            "vacuum",
            "start",
            service_data={"entity_id": entity_id},
        )

        return HandleOutput(success=True)
