from ..const import VacuumEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class VacuumCleanAreaHandler(IntentHandler):
    intent_type = "HassVacuumCleanArea"
    match_targets = True
    inferred_domain = "vacuum"
    required_features = VacuumEntityFeature.CLEAN_AREA

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        area_id = handle_input.intent_result.entities["area"].value
        if handle_input.target_entity_ids:
            entity_id = handle_input.target_entity_ids[0]
        else:
            entity_id = "all"

        await handle_input.hass.call_service(
            "vacuum",
            "clean_area",
            service_data={"entity_id": entity_id, "cleaning_area_id": area_id},
        )

        return HandleOutput(success=True)
