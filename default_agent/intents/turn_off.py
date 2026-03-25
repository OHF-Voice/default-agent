from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class TurnOffHandler(IntentHandler):
    intent_type = "HassTurnOff"
    match_targets = True

    async def handle(self, input: HandleInput) -> HandleOutput:
        domain = input.match_domain or "homeassistant"

        if domain == "cover":
            service = "close_cover"
        elif domain == "valve":
            service = "close_valve"
        elif domain == "lock":
            service = "unlock"
        else:
            service = "turn_off"

        await input.hass.call_service(
            domain, service, target={"entity_id": input.target_entity_ids}
        )

        return HandleOutput(success=True)