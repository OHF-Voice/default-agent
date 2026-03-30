from ..const import MediaPlayerEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class MediaNextHandler(IntentHandler):
    intent_type = "HassMediaNext"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "playing"
    required_features = MediaPlayerEntityFeature.NEXT_TRACK

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        await handle_input.hass.call_service(
            "media_player",
            "media_next_track",
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
