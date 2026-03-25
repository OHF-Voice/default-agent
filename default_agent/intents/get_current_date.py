from datetime import datetime

from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class GetCurrentDateHandler(IntentHandler):
    intent_type = "HassGetCurrentDate"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        return HandleOutput(success=True, response_vars={"date": datetime.now()})
