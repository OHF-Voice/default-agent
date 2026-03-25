from ..intent_handler import IntentHandler, HandleInput, HandleOutput
from enum import IntFlag


class VacuumEntityFeature(IntFlag):
    TURN_ON = 1
    TURN_OFF = 2
    PAUSE = 4
    STOP = 8
    RETURN_HOME = 16
    FAN_SPEED = 32
    BATTERY = 64
    STATUS = 128
    SEND_COMMAND = 256
    LOCATE = 512
    CLEAN_SPOT = 1024
    MAP = 2048
    STATE = 4096
    START = 8192
    CLEAN_AREA = 16384


class VacuumCleanAreaHandler(IntentHandler):
    intent_type = "HassVacuumCleanArea"
    match_targets = True
    inferred_domain = "vacuum"
    required_features = VacuumEntityFeature.CLEAN_AREA

    async def handle(self, input: HandleInput) -> HandleOutput:
        area_id = input.intent_result.entities["area"].value
        if input.target_entity_ids:
            entity_id = input.target_entity_ids[0]
        else:
            entity_id = "all"

        await input.hass.call_service(
            "vacuum",
            "return_to_base",
            service_data={"entity_id": entity_id, "cleaning_area_id": area_id},
        )

        return HandleOutput(success=True)