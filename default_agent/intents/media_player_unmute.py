from enum import IntFlag

from ..intent_handler import HandleInput, HandleOutput, IntentHandler


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
