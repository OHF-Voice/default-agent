from ..intent_handler import IntentHandler, HandleInput, HandleOutput
from enum import IntFlag


class MediaPlayerEntityFeature(IntFlag):
    PAUSE = 1
    SEEK = 2
    VOLUME_SET = 4
    VOLUME_MUTE = 8
    PREVIOUS_TRACK = 16
    NEXT_TRACK = 32
    TURN_ON = 128
    TURN_OFF = 256
    PLAY_MEDIA = 512
    VOLUME_STEP = 1024
    SELECT_SOURCE = 2048
    STOP = 4096
    CLEAR_PLAYLIST = 8192
    PLAY = 16384
    SHUFFLE_SET = 32768
    SELECT_SOUND_MODE = 65536
    BROWSE_MEDIA = 131072
    REPEAT_SET = 262144
    GROUPING = 524288
    MEDIA_ANNOUNCE = 1048576
    MEDIA_ENQUEUE = 2097152
    SEARCH_MEDIA = 4194304


class SetVolumeHandler(IntentHandler):
    intent_type = "HassSetVolume"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "playing"
    required_features = MediaPlayerEntityFeature.VOLUME_SET

    async def handle(self, input: HandleInput) -> HandleOutput:
        volume_level = float(input.intent_result.entities["volume_level"].value) / 100
        volume_level = max(0, min(1, volume_level))

        await input.hass.call_service(
            "media_player",
            "volume_set",
            service_data={"volume_level": volume_level},
            target={"entity_id": input.target_entity_ids},
        )

        return HandleOutput(success=True)