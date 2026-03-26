from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class NevermindHandler(IntentHandler):
    intent_type = "HassNevermind"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        return HandleOutput(success=True)
