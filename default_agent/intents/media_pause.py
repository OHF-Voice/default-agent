"""Intent handler for HassMediaPause."""

from ..const import MediaPlayerEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class MediaPauseHandler(IntentHandler):
    intent_type = "HassMediaPause"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "playing"
    required_features = MediaPlayerEntityFeature.PAUSE

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        await handle_input.hass.call_service(
            "media_player",
            "media_pause",
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
