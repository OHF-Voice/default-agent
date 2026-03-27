from typing import Any, Dict

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class UnpauseTimerHandler(IntentHandler):
    intent_type = "HassUnpauseTimer"
    match_targets = False

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        start_hours_value = handle_input.intent_result.entities.get("start_hours")
        start_minutes_value = handle_input.intent_result.entities.get("start_minutes")
        start_seconds_value = handle_input.intent_result.entities.get("start_seconds")
        name_value = handle_input.intent_result.entities.get("name")

        data: Dict[str, Any] = {}
        if start_hours_value is not None:
            data["start_hours"] = int(start_hours_value.value)
        if start_minutes_value is not None:
            data["start_minutes"] = int(start_minutes_value.value)
        if start_seconds_value is not None:
            data["start_seconds"] = int(start_seconds_value.value)
        if name_value is not None:
            data["name"] = name_value.value

        await handle_input.hass.run_command("intent/unpause_timer", data)

        return HandleOutput(success=True)
