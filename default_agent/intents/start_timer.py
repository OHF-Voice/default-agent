from typing import Any, Dict

from hassil import recognize

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class StartTimerHandler(IntentHandler):
    intent_type = "HassStartTimer"
    match_targets = False

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        hours_value = handle_input.intent_result.entities.get("hours")
        minutes_value = handle_input.intent_result.entities.get("minutes")
        seconds_value = handle_input.intent_result.entities.get("seconds")
        name_value = handle_input.intent_result.entities.get("name")
        conversation_command_value = handle_input.intent_result.entities.get(
            "conversation_command"
        )

        data: Dict[str, Any] = {}
        if hours_value is not None:
            data["hours"] = int(hours_value.value)
        if minutes_value is not None:
            data["minutes"] = int(minutes_value.value)
        if seconds_value is not None:
            data["seconds"] = int(seconds_value.value)
        if name_value is not None:
            data["name"] = name_value.value
        if conversation_command_value is not None:
            # validate conversation_command
            conversation_command = str(conversation_command_value.value)
            is_recognized = (
                recognize(
                    conversation_command,
                    handle_input.lang_intents.intents,
                    slot_lists=handle_input.hass_info.slot_lists,
                    language=handle_input.language,
                )
                is not None
            )
            if not is_recognized:
                # TODO: Add an error message for this
                return HandleOutput(
                    success=False, response_text="Command would not be recognized"
                )

            data["conversation_command"] = conversation_command

        await handle_input.hass.handle_intent(
            self.intent_type,
            handle_input.language,
            data=data,
            device_id=handle_input.device_id,
            satellite_id=handle_input.satellite_id,
        )
        return HandleOutput(success=True)
