from datetime import datetime

from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class GetCurrentTimeHandler(IntentHandler):
    intent_type = "HassGetCurrentTime"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        return HandleOutput(success=True, response_vars={"time": datetime.now()})
