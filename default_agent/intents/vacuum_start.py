from enum import IntFlag

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


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
