from ..const import MediaPlayerEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class MediaUnpauseHandler(IntentHandler):
    intent_type = "HassMediaUnpause"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "paused"
    required_features = MediaPlayerEntityFeature.PLAY

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        await handle_input.hass.call_service(
            "media_player",
            "media_play",
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
