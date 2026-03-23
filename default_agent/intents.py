from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from hassil import RecognizeResult

from .hass_api import HomeAssistant
from .name_matcher import MatchTargetsResult
from .models import State


@dataclass
class IntentHandledResult:
    matched_states: List[State]
    unmatched_states: List[State]
    speech_slots: Dict[str, Any]


async def async_handle_intent(
    hass: HomeAssistant,
    intent_result: RecognizeResult,
    match_result: MatchTargetsResult,
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

        print(domain, service, domain_value)
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

    if intent_name == "HassSetPosition":
        await hass.trigger_service(
            "cover",
            "set_position",
            service_data={"position": intent_result.entities["position"].value},
            target={"entity_id": entity_ids},
        )
        return result

    return None
