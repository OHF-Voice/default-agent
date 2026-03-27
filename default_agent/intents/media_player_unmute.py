from ..const import MediaPlayerEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class MediaPlayerUnmuteHandler(IntentHandler):
    intent_type = "HassMediaPlayerUnmute"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "playing"
    required_features = MediaPlayerEntityFeature.VOLUME_MUTE

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        await handle_input.hass.call_service(
            "media_player",
            "volume_mute",
            service_data={"is_volume_muted": False},
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
