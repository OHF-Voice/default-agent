from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class GetWeatherHandler(IntentHandler):
    intent_type = "HassGetWeather"
    match_targets = True
    inferred_domain = "weather"

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        return HandleOutput(success=True)
