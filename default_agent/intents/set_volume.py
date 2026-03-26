from ..const import MediaPlayerEntityFeature
from ..intent_handler import HandleInput, HandleOutput, IntentHandler


class SetVolumeHandler(IntentHandler):
    intent_type = "HassSetVolume"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "playing"
    required_features = MediaPlayerEntityFeature.VOLUME_SET

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        volume_level = (
            float(handle_input.intent_result.entities["volume_level"].value) / 100
        )
        volume_level = max(0, min(1, volume_level))

        await handle_input.hass.call_service(
            "media_player",
            "volume_set",
            service_data={"volume_level": volume_level},
            target={"entity_id": handle_input.target_entity_ids},
        )

        return HandleOutput(success=True)
