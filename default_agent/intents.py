from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from hassil import RecognizeResult

from .hass_api import HomeAssistant, InfoForRecognition
from .models import State
from .name_matcher import MatchTargetsResult
from .util import (
    MediaPlayerEntityFeature,
    color_name_to_rgb,
    VacuumEntityFeature,
    FanEntityFeature,
)

INTENT_DOMAINS: Dict[str, Union[str, Set[str]]] = {
    "HassLightSet": "light",
    "HassGetWeather": "weather",
    #
    "HassVacuumStart": "vacuum",
    "HassVacuumReturnToBase": "vacuum",
    "HassVacuumCleanArea": "vacuum",
    #
    "HassMediaPause": "media_player",
    "HassMediaUnpause": "media_player",
    "HassMediaNext": "media_player",
    "HassMediaPrevious": "media_player",
    "HassMediaSearchAndPlay": "media_player",
    "HassMediaPlayerMute": "media_player",
    "HassMediaPlayerUnmute": "media_player",
    "HassSetVolume": "media_player",
    "HassSetVolumeRelative": "media_player",
    #
    "HassFanSetSpeed": "fan",
    #
    "HassLawnMowerStartMowing": "lawn_mower",
    "HassLawnMowerDock": "lawn_mower",
}

INTENT_SUPPORTED_FEATURES: Dict[str, int] = {
    "HassVacuumStart": VacuumEntityFeature.START,
    "HassVacuumReturnToBase": VacuumEntityFeature.RETURN_HOME,
    "HassVacuumCleanArea": VacuumEntityFeature.CLEAN_AREA,
    #
    "HassMediaPause": MediaPlayerEntityFeature.PAUSE,
    "HassMediaUnpause": MediaPlayerEntityFeature.PLAY,
    "HassMediaNext": MediaPlayerEntityFeature.NEXT_TRACK,
    "HassMediaPrevious": MediaPlayerEntityFeature.PREVIOUS_TRACK,
    "HassMediaSearchAndPlay": MediaPlayerEntityFeature.SEARCH_MEDIA
    & MediaPlayerEntityFeature.PLAY,
    "HassMediaPlayerMute": MediaPlayerEntityFeature.VOLUME_MUTE,
    "HassMediaPlayerUnmute": MediaPlayerEntityFeature.VOLUME_MUTE,
    "HassSetVolume": MediaPlayerEntityFeature.VOLUME_SET,
    "HassSetVolumeRelative": MediaPlayerEntityFeature.VOLUME_SET,
    #
    "HassFanSetSpeed": FanEntityFeature.SET_SPEED,
}

INTENT_STATES: Dict[str, Union[str, Set[str]]] = {
    "HassMediaPause": "playing",
    "HassMediaUnpause": "paused",
    "HassMediaNext": "playing",
    "HassMediaPrevious": "playing",
    "HassMediaPlayerMute": "playing",
    "HassMediaPlayerUnmute": "playing",
    "HassSetVolume": "playing",
    "HassSetVolumeRelative": "playing",
}


@dataclass
class IntentHandledResult:
    matched_states: List[State]
    unmatched_states: List[State]
    speech_slots: Dict[str, Any]


async def async_handle_intent(
    hass: HomeAssistant,
    *,
    intent_result: RecognizeResult,
    match_result: MatchTargetsResult,
    hass_info: InfoForRecognition,
    language: str,
    device_id: Optional[str] = None,
    satellite_id: Optional[str] = None,
) -> Optional[IntentHandledResult]:
    intent_name = intent_result.intent.name
    entity_ids = [s.entity_id for s in match_result.states]
    result = IntentHandledResult(
        matched_states=match_result.states, unmatched_states=[], speech_slots={}
    )

    if intent_name == "HassNevermind":
        return result

    if intent_name == "HassGetCurrentTime":
        result.speech_slots["time"] = datetime.now()
        return result

    if intent_name == "HassGetCurrentDate":
        result.speech_slots["date"] = datetime.now()
        return result

    if intent_name in ("HassTurnOn", "HassTurnOff"):
        domain_value = intent_result.entities.get("domain")
        if domain_value:
            domain = domain_value.value
        else:
            domain = intent_result.context.get("domain", "homeassistant")

        if intent_name == "HassTurnOn":
            # on/open/lock
            if domain == "cover":
                service = "open_cover"
            elif domain == "valve":
                service = "open_valve"
            elif domain == "lock":
                service = "lock"
            else:
                service = "turn_on"
        else:
            # off/close/unlock
            if domain == "cover":
                service = "close_cover"
            elif domain == "valve":
                service = "close_valve"
            elif domain == "lock":
                service = "unlock"
            else:
                service = "turn_off"

        await hass.trigger_service(domain, service, target={"entity_id": entity_ids})
        return result

    if intent_name == "HassTurnOff":
        # off/close/unlock
        await hass.trigger_service(
            "homeassistant", "turn_off", target={"entity_id": entity_ids}
        )
        return result

    # TODO: HassGetState
    # TODO: HassRespond
    # TODO: HassBroadcast

    # cover
    if intent_name == "HassSetPosition":
        # set position percentage of a cover
        position = int(intent_result.entities["position"].value)
        await hass.trigger_service(
            "cover",
            "set_cover_position",
            service_data={"position": position},
            target={"entity_id": entity_ids},
        )
        return result

    # light
    if intent_name == "HassLightSet":
        # set light brightness/color
        brightness_value = intent_result.entities.get("brightness")
        color_value = intent_result.entities.get("color")
        temperature_value = intent_result.entities.get("temperature")

        service_data: Dict[str, Any] = {}
        if brightness_value:
            service_data["brightness_pct"] = int(brightness_value.value)

        if color_value:
            service_data["rgb_color"] = color_name_to_rgb(color_value.value)

        if temperature_value:
            service_data["color_temp_kelvin"] = int(temperature_value.value)

        await hass.trigger_service(
            "light",
            "turn_on",
            service_data=service_data,
            target={"entity_id": entity_ids},
        )
        return result

    # TODO: HassClimateGetTemperature
    # TODO: HassClimateSetTemperature

    # TODO: HassShoppingListAddItem
    # TODO: HassShoppingListCompleteItem

    # weather
    if intent_name == "HassGetWeather":
        # first matched has weather entity state
        return result

    # todo
    if intent_name == "HassListAddItem":
        item = intent_result.entities["item"].value
        await hass.trigger_service(
            "todo",
            "add_item",
            service_data={"item": item},
            target={"entity_id": entity_ids},
        )
        return result

    if intent_name == "HassListCompleteItem":
        item = intent_result.entities["item"].value
        await hass.trigger_service(
            "todo",
            "update_item",
            service_data={"item": item, "status": "completed"},
            target={"entity_id": entity_ids},
        )
        return result

    if intent_name == "HassListRemoveItem":
        item = intent_result.entities["item"].value
        await hass.trigger_service(
            "todo",
            "remove_item",
            service_data={"item": item},
            target={"entity_id": entity_ids},
        )
        return result

    # vacuum
    if intent_name == "HassVacuumStart":
        if entity_ids:
            entity_id = entity_ids[0]
        else:
            entity_id = "all"

        await hass.trigger_service(
            "vacuum",
            "start",
            service_data={"entity_id": entity_id},
        )
        return result

    if intent_name == "HassVacuumReturnToBase":
        if entity_ids:
            entity_id = entity_ids[0]
        else:
            entity_id = "all"

        await hass.trigger_service(
            "vacuum",
            "return_to_base",
            service_data={"entity_id": entity_id},
        )
        return result

    if intent_name == "HassVacuumCleanArea":
        area_id = intent_result.entities["area"].value
        if entity_ids:
            entity_id = entity_ids[0]
        else:
            entity_id = "all"

        await hass.trigger_service(
            "vacuum",
            "return_to_base",
            service_data={"entity_id": entity_id, "cleaning_area_id": area_id},
        )
        return result

    # media
    if intent_name == "HassMediaPause":
        await hass.trigger_service(
            "media_player", "media_pause", target={"entity_id": entity_ids}
        )
        return result

    if intent_name == "HassMediaUnpause":
        await hass.trigger_service(
            "media_player", "media_play", target={"entity_id": entity_ids}
        )
        return result

    if intent_name == "HassMediaNext":
        await hass.trigger_service(
            "media_player", "media_next_track", target={"entity_id": entity_ids}
        )
        return result

    if intent_name == "HassMediaPrevious":
        await hass.trigger_service(
            "media_player", "media_previous_track", target={"entity_id": entity_ids}
        )
        return result

    if intent_name == "HassMediaPlayerMute":
        await hass.trigger_service(
            "media_player",
            "volume_mute",
            service_data={"is_volume_muted": True},
            target={"entity_id": entity_ids},
        )
        return result

    if intent_name == "HassMediaPlayerUnmute":
        await hass.trigger_service(
            "media_player",
            "volume_mute",
            service_data={"is_volume_muted": False},
            target={"entity_id": entity_ids},
        )
        return result

    if intent_name == "HassSetVolume":
        volume_level = float(intent_result.entities["volume_level"].value) / 100
        volume_level = max(0, min(1, volume_level))

        await hass.trigger_service(
            "media_player",
            "volume_set",
            service_data={"volume_level": volume_level},
            target={"entity_id": entity_ids},
        )
        return result

    if intent_name == "HassSetVolumeRelative":
        volume_step = intent_result.entities["volume_step"].value
        for entity_id in entity_ids:
            state = hass_info.states.get(entity_id)
            if state is None:
                continue

            volume_level = state.attributes.get("volume_level")
            if volume_level is None:
                continue

            if volume_step == "up":
                volume_level += 0.1  # 10%
            elif volume_step == "down":
                volume_level -= 0.1  # 10%
            else:
                volume_level += float(volume_step) / 100

            volume_level = max(0, min(1, volume_level))

            await hass.trigger_service(
                "media_player",
                "volume_set",
                service_data={"volume_level": volume_level},
                target={"entity_id": entity_id},
            )
        return result

    # TODO: HassMediaSearchAndPlay

    # TODO: timers
    if intent_name == "HassStartTimer":
        await hass.handle_intent(
            intent_result,
            language=language,
            device_id=device_id,
            satellite_id=satellite_id,
        )
        return result

    if intent_name == "HassFanSetSpeed":
        percentage = int(intent_result.entities["percentage"].value)

        await hass.trigger_service(
            "fan",
            "set_percentage",
            service_data={"percentage": percentage},
            target={"entity_id": entity_ids},
        )
        return result

    # TODO: lawn mowers

    return None
