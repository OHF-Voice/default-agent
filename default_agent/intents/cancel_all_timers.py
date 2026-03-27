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

        command_result = await handle_input.hass.run_command(
            "intent/cancel_all_timers", data
        )
        timer_ids = command_result.get("timer_ids", [])

        return HandleOutput(success=True, response_vars={"canceled": len(timer_ids)})
