from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class TurnOnHandler(IntentHandler):
    intent_type = "HassTurnOn"
    match_targets = True

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        domain = handle_input.match_domain or "homeassistant"

        # on/open/lock
        if domain == "cover":
            service = "open_cover"
        elif domain == "valve":
            service = "open_valve"
        elif domain == "lock":
            service = "lock"
        else:
            service = "turn_on"

        await handle_input.hass.call_service(
            domain, service, target={"entity_id": handle_input.target_entity_ids}
        )

        return HandleOutput(success=True)
