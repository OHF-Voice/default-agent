from datetime import datetime

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class GetCurrentDateHandler(IntentHandler):
    intent_type = "HassGetCurrentDate"
    match_targets = False

    async def handle(self, input: HandleInput) -> HandleOutput:
        return HandleOutput(success=True, response_vars={"date": datetime.now()})
