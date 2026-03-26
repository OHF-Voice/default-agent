from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class StartTimerHandler(IntentHandler):
    intent_type = "HassStartTimer"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        return HandleOutput(success=True)
