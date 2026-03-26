from typing import Any, Dict

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class CancelAllTimersHandler(IntentHandler):
    intent_type = "HassCancelAllTimers"
    match_targets = False

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        area_value = handle_input.intent_result.entities.get("area")

        data: Dict[str, Any] = {}
        if area_value is not None:
            data["area"] = area_value.value

        await handle_input.hass.handle_intent(
            self.intent_type,
            handle_input.language,
            data=data,
            device_id=handle_input.device_id,
            satellite_id=handle_input.satellite_id,
        )

        # TODO: find out how many timers were canceled

        return HandleOutput(success=True, response_vars={"canceled": 0})
