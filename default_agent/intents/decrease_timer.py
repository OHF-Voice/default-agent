from typing import Any, Dict

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class DecreaseTimerHandler(IntentHandler):
    intent_type = "HassDecreaseTimer"
    match_targets = False

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        start_hours_value = handle_input.intent_result.entities.get("start_hours")
        start_minutes_value = handle_input.intent_result.entities.get("start_minutes")
        start_seconds_value = handle_input.intent_result.entities.get("start_seconds")
        name_value = handle_input.intent_result.entities.get("name")
        hours_value = handle_input.intent_result.entities.get("hours")
        minutes_value = handle_input.intent_result.entities.get("minutes")
        seconds_value = handle_input.intent_result.entities.get("seconds")

        data: Dict[str, Any] = {}
        if start_hours_value is not None:
            data["start_hours"] = int(start_hours_value.value)
        if start_minutes_value is not None:
            data["start_minutes"] = int(start_minutes_value.value)
        if start_seconds_value is not None:
            data["start_seconds"] = int(start_seconds_value.value)
        if name_value is not None:
            data["name"] = name_value.value
        if hours_value is not None:
            data["hours"] = int(hours_value.value)
        if minutes_value is not None:
            data["minutes"] = int(minutes_value.value)
        if seconds_value is not None:
            data["seconds"] = int(seconds_value.value)

        await handle_input.hass.run_command("intent/decrease_timer", data)

        return HandleOutput(success=True)
