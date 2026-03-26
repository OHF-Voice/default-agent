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


class SetVolumeRelativeHandler(IntentHandler):
    intent_type = "HassSetVolumeRelative"
    match_targets = True
    inferred_domain = "media_player"
    required_states = "playing"
    required_features = MediaPlayerEntityFeature.VOLUME_SET

    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        volume_step = handle_input.intent_result.entities["volume_step"].value
        for entity_id in handle_input.target_entity_ids:
            state = handle_input.hass_info.states.get(entity_id)
            if state is None:
                continue

            volume_level = state.attributes.get("volume_level")
            if volume_level is None:
                continue

            if volume_step == "up":
                volume_level += 0.1
            elif volume_step == "down":
                volume_level -= 0.1
            else:
                volume_level += float(volume_step) / 100

            volume_level = max(0, min(1, volume_level))

            await handle_input.hass.call_service(
                "media_player",
                "volume_set",
                service_data={"volume_level": volume_level},
                target={"entity_id": entity_id},
            )

        return HandleOutput(success=True)
