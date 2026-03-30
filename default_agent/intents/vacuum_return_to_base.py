from ..const import VacuumEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class VacuumReturnToBaseHandler(IntentHandler):
    intent_type = "HassVacuumReturnToBase"
    match_targets = True
    inferred_domain = "vacuum"
    required_features = VacuumEntityFeature.RETURN_HOME

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        if handle_input.target_entity_ids:
            entity_id = handle_input.target_entity_ids[0]
        else:
            entity_id = "all"

        await handle_input.hass.call_service(
            "vacuum",
            "return_to_base",
            service_data={"entity_id": entity_id},
        )

        return HandleOutput(success=True)
