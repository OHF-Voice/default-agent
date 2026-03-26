from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class TurnOffHandler(IntentHandler):
    intent_type = "HassTurnOff"
    match_targets = True

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        domain = handle_input.match_domain or "homeassistant"

        if domain == "cover":
            service = "close_cover"
        elif domain == "valve":
            service = "close_valve"
        elif domain == "lock":
            service = "unlock"
        else:
            service = "turn_off"

        await handle_input.hass.call_service(
            domain, service, target={"entity_id": handle_input.target_entity_ids}
        )

        return HandleOutput(success=True)
