"""Default agent implementation."""

import itertools
import logging
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from hassil import RecognizeResult, recognize_best
from home_assistant_intents import ErrorKey
from jinja2 import BaseLoader, Environment, StrictUndefined

from .hass_api import HomeAssistant, InfoForRecognition
from .intents_loader import LanguageIntents

_LOGGER = logging.getLogger(__name__)

_DEFAULT_ERROR_TEXT = "Sorry, I couldn't understand that."
_ENV = Environment(loader=BaseLoader(), undefined=StrictUndefined)


class MatchFailedReason(str, Enum):
    """Possible reasons for match failure.

    Must align with homeassistant.helpers.intent.MatchFailedReason
    """

    NAME = "NAME"
    """No entities matched name constraint."""

    AREA = "AREA"
    """No entities matched area constraint."""

    FLOOR = "FLOOR"
    """No entities matched floor constraint."""

    DOMAIN = "DOMAIN"
    """No entities matched domain constraint."""

    DEVICE_CLASS = "DEVICE_CLASS"
    """No entities matched device class constraint."""

    FEATURE = "FEATURE"
    """No entities matched supported features constraint."""

    STATE = "STATE"
    """No entities matched required states constraint."""

    ASSISTANT = "ASSISTANT"
    """No entities matched exposed to assistant constraint."""

    INVALID_AREA = "INVALID_AREA"
    """Area name from constraint does not exist."""

    INVALID_FLOOR = "INVALID_FLOOR"
    """Floor name from constraint does not exist."""

    DUPLICATE_NAME = "DUPLICATE_NAME"
    """Two or more entities matched the same name constraint and could not be disambiguated."""

    MULTIPLE_TARGETS = "MULTIPLE_TARGETS"
    """Two or more entities matched when a single target is required."""


@dataclass
class MatchTargetsConstraints:
    """Constraints for async_match_targets.

    Used here to determine error message.
    """

    name: str | None = None
    """Entity name or alias."""

    area_name: str | None = None
    """Area name, id, or alias."""

    floor_name: str | None = None
    """Floor name, id, or alias."""

    domains: Collection[str] | None = None
    """Domain names."""

    device_classes: Collection[str] | None = None
    """Device class names."""

    features: int | None = None
    """Required supported features."""

    states: Collection[str] | None = None
    """Required states for entities."""

    assistant: str | None = None
    """Name of assistant that entities should be exposed to."""

    allow_duplicate_names: bool = False
    """True if entities with duplicate names are allowed in result."""

    single_target: bool = False
    """True if result must contain a single target."""


async def async_converse(
    hass: HomeAssistant,
    text: str,
    lang_intents: LanguageIntents,
    device_id: Optional[str] = None,
    satellite_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Tries to recognize intent from text and handle intent.

    If successful, returns (True, response).
    Otherwise, returns (False, error)."""

    # Get exposed entities, etc.
    #
    # We load these each time to avoid subscribing to state changes over the
    # websocket API.
    # This will be slower with many exposed entities, but this agent is intended
    # to run in a Home Assistant app/add-on with virtually no latency.
    _LOGGER.debug("Loading entities from Home Assistant")
    hass_info = await hass.get_info(device_id=device_id, satellite_id=satellite_id)

    # Build intent context
    intent_context: Dict[str, Any] = {}
    if hass_info.preferred_area_id and hass_info.preferred_area_name:
        intent_context["area"] = {
            "name": hass_info.preferred_area_name,
            "value": hass_info.preferred_area_id,
        }

    # Recognize intent
    _LOGGER.debug(
        "Recognizing intent for text (language=%s): %s", lang_intents.language, text
    )
    result = recognize_best(
        text,
        lang_intents.intents,
        slot_lists=hass_info.slot_lists,
        intent_context=intent_context,
        language=lang_intents.language,
        best_slot_name="name",
    )  # TODO: prefer custom sentences with "best_metadata_key"
    if result is None:
        # TODO: re-run with unmatched entities?
        _LOGGER.debug(
            "No intent recognized for text (language=%s): %s",
            lang_intents.language,
            text,
        )
        return (False, render_error(lang_intents, ErrorKey.NO_INTENT))

    # Run the intent handler in Home Assistant
    extra_data: Dict[str, Any] = {}
    if hass_info.preferred_area_id:
        extra_data["preferred_area_id"] = hass_info.preferred_area_id

    if hass_info.preferred_floor_id:
        extra_data["preferred_floor_id"] = hass_info.preferred_floor_id

    # /api/intent/handle
    intent_response = await hass.handle_intent(
        result,
        language=lang_intents.language,
        device_id=device_id,
        satellite_id=satellite_id,
        extra_data=extra_data,
    )
    _LOGGER.debug("Intent response: %s", intent_response)

    if intent_response.get("response_type") == "error":
        # Intent failed in Home Assistant
        return (False, get_intent_response_error(lang_intents, intent_response))

    # Check if intent handler in Home Assistant produced a response
    speech = (
        intent_response.get("speech", {}).get("plain", {}).get("speech", "").strip()
    )
    if speech:
        # Intent already has a response
        return (True, speech)

    # Render built-in response
    return (True, render_response(result, intent_response, lang_intents, hass_info))


def render_response(
    result: RecognizeResult,
    intent_response: Dict[str, Any],
    lang_intents: LanguageIntents,
    info: InfoForRecognition,
) -> str:
    """Render the response Jinja2 template for the intent.

    This is done locally rather than in Home Assistant, so we need to patch
    things to keep the Jinja2 environment compatible with existing response
    templates.
    """
    # result.response is a key into the intent's response templates
    response_template = lang_intents.intent_responses.get(result.intent.name, {}).get(
        result.response
    )
    if not response_template:
        # No response template
        return ""

    slots: Dict[str, Any] = {e.name: e.value for e in result.entities_list}
    speech_slots = intent_response.get("speech_slots")
    if speech_slots:
        slots.update(speech_slots)

    def state_attr(entity_id: str, attr_name: str) -> Any:
        return info.entity_attributes.get(entity_id, {}).get(attr_name)

    variables: Dict[str, Any] = {"slots": slots, "state_attr": state_attr}

    # Patch for specific intents.
    #
    # We do this because the "speech slot" values set by the intent handler in
    # Home Assistant were transformed into JSON via the REST API, but the
    # response templates assume the original objects exist.
    #
    # For example, "HassGetCurrentTime" assumes a Python datetime object in
    # slots.time, but we get back an ISO time string from the REST API.
    intent_response_data = intent_response.get("data", {})
    if result.intent.name == "HassGetCurrentTime":
        # ISO -> time
        time_str = slots.get("time")
        if isinstance(time_str, str):
            slots["time"] = time.fromisoformat(time_str)
    elif result.intent.name == "HassGetCurrentDate":
        # ISO -> datetime
        date_str = slots.get("date")
        if isinstance(date_str, str):
            slots["date"] = datetime.fromisoformat(date_str)

    # The "query" field is mainly used by HassGetState to tell which entities
    # matched the question.
    #
    # If the users asks "is the bedroom light on", its state will show up in
    # "matched" if it's state is "on" and in "unmatched" if it's not.
    query = intent_response_data.get("query", {})
    matched = query.get("matched", [])
    unmatched = query.get("unmatched", [])
    first_state = None
    for state in itertools.chain(matched, unmatched):
        if first_state is None:
            first_state = state

        entity_id = state["entity_id"]
        state["state_with_unit"] = state["state"]
        state["domain"] = entity_id.split(".", maxsplit=1)[0]
        state["attributes"] = info.entity_attributes.get(entity_id, {})

    variables["query"] = query
    if first_state is not None:
        # The first matched or unmatched entity is available as "state".
        variables["state"] = first_state

    # TODO: We're using StrictUndefined for Jinja2 rendering right now.
    # We may want to consider making undefined objects "falsey" like Home
    # Assistant does.
    _LOGGER.debug(
        "Rendering response '%s' with variables %s: %s",
        result.response,
        variables,
        response_template,
    )
    response_str = _ENV.from_string(response_template).render(variables)

    # Normalize whitespace
    response_str = " ".join(response_str.split()).strip()

    return response_str


def render_error(
    lang_intents: LanguageIntents, key: ErrorKey, data: Optional[Dict[str, Any]] = None
) -> str:
    """Render a Jinja2 template for a pre-defined error.

    These are found in the language's sentences/_common.yaml file.
    """
    error_template = lang_intents.error_responses.get(key.value)
    if not error_template:
        return _DEFAULT_ERROR_TEXT

    if data is None:
        data = {}

    error_text = _ENV.from_string(error_template).render(data)

    # Normalize whitespace
    error_text = " ".join(error_text.split()).strip()

    return error_text


def get_intent_response_error(
    lang_intents: LanguageIntents, intent_response: Dict[str, Any]
) -> str:
    """Return the error text for a match failure."""
    error_text = (
        intent_response.get("speech", {}).get("plain", {}).get("speech", "")
    ).strip()
    if error_text:
        # Response already contains error message
        return error_text

    match_error: Optional[Dict[str, Any]] = intent_response.get("data", {}).get(
        "match_error"
    )
    if not match_error:
        # No more information about why the intent failed
        return _DEFAULT_ERROR_TEXT

    error_key, error_data = get_match_error_response(match_error)

    return render_error(lang_intents, error_key, error_data)


def get_match_error_response(
    match_error: Dict[str, Any],
) -> Tuple[ErrorKey, Dict[str, Any]]:
    """Return key and template arguments for error when target matching fails.

    Unfortunately, the error information is not always precise enough to know
    exactly what went wrong. This is due to how async_match_targets works in
    Home Assistant to find entities by name given certain constraints.

    For example, say we have two exposed media players in Home Assistant:
    - Media player 1 is in the current area but doesn't support NEXT_TRACK
    - Media player 2 is in a different area and supports NEXT_TRACK

    If we give the command "next track", this implies two constraints:
    1. The media player must support NEXT_TRACK
    2. The media player must be in the current area
    3. The media player must be in the "playing" state

    Assuming both media players are "playing", async_match_targets will:
    1. Begin with two candidates: media player 1 and media player 2
    2. Eliminate media player 2 because it doesn't support the required feature
    3. Check if media player 2 is in the current area
    4. Fail with the "AREA" MatchFailedReason

    When figuring out the error message, we don't have enough information to
    know that the real problem is media player 1 doesn't supported NEXT_TRACK
    because we only see why the *last* candidate was eliminated.
    """

    constraints = MatchTargetsConstraints(**match_error["constraints"])
    reason = MatchFailedReason(match_error["no_match_reason"])
    no_match_name = match_error.get("no_match_name")

    if (
        reason in (MatchFailedReason.DEVICE_CLASS, MatchFailedReason.DOMAIN)
    ) and constraints.device_classes:
        device_class = next(iter(constraints.device_classes))  # first device class
        if constraints.area_name:
            # device_class in area
            return ErrorKey.NO_DEVICE_CLASS_IN_AREA, {
                "device_class": device_class,
                "area": constraints.area_name,
            }

        # device_class only
        return ErrorKey.NO_DEVICE_CLASS, {"device_class": device_class}

    if (reason == MatchFailedReason.DOMAIN) and constraints.domains:
        domain = next(iter(constraints.domains))  # first domain
        if constraints.area_name:
            # domain in area
            return ErrorKey.NO_DOMAIN_IN_AREA, {
                "domain": domain,
                "area": constraints.area_name,
            }

        if constraints.floor_name:
            # domain in floor
            return ErrorKey.NO_DOMAIN_IN_FLOOR, {
                "domain": domain,
                "floor": constraints.floor_name,
            }

        # domain only
        return ErrorKey.NO_DOMAIN, {"domain": domain}

    if reason == MatchFailedReason.DUPLICATE_NAME:
        if constraints.floor_name:
            # duplicate on floor
            return ErrorKey.DUPLICATE_ENTITIES_IN_FLOOR, {
                "entity": no_match_name,
                "floor": constraints.floor_name,
            }

        if constraints.area_name:
            # duplicate on area
            return ErrorKey.DUPLICATE_ENTITIES_IN_AREA, {
                "entity": no_match_name,
                "area": constraints.area_name,
            }

        return ErrorKey.DUPLICATE_ENTITIES, {"entity": no_match_name}

    if reason == MatchFailedReason.INVALID_AREA:
        # Invalid area name
        return ErrorKey.NO_AREA, {"area": no_match_name}

    if reason == MatchFailedReason.INVALID_FLOOR:
        # Invalid floor name
        return ErrorKey.NO_FLOOR, {"floor": no_match_name}

    if reason == MatchFailedReason.FEATURE:
        # Feature not supported by entity
        return ErrorKey.FEATURE_NOT_SUPPORTED, {}

    if reason == MatchFailedReason.STATE:
        # Entity is not in correct state
        assert constraints.states
        state = next(iter(constraints.states))

        return ErrorKey.ENTITY_WRONG_STATE, {"state": state}

    if reason == MatchFailedReason.ASSISTANT:
        # Not exposed
        if constraints.name:
            if constraints.area_name:
                return ErrorKey.NO_ENTITY_IN_AREA_EXPOSED, {
                    "entity": constraints.name,
                    "area": constraints.area_name,
                }
            if constraints.floor_name:
                return ErrorKey.NO_ENTITY_IN_FLOOR_EXPOSED, {
                    "entity": constraints.name,
                    "floor": constraints.floor_name,
                }
            return ErrorKey.NO_ENTITY_EXPOSED, {"entity": constraints.name}

        if constraints.device_classes:
            device_class = next(iter(constraints.device_classes))

            if constraints.area_name:
                return ErrorKey.NO_DEVICE_CLASS_IN_AREA_EXPOSED, {
                    "device_class": device_class,
                    "area": constraints.area_name,
                }
            if constraints.floor_name:
                return ErrorKey.NO_DEVICE_CLASS_IN_FLOOR_EXPOSED, {
                    "device_class": device_class,
                    "floor": constraints.floor_name,
                }
            return ErrorKey.NO_DEVICE_CLASS_EXPOSED, {"device_class": device_class}

        if constraints.domains:
            domain = next(iter(constraints.domains))

            if constraints.area_name:
                return ErrorKey.NO_DOMAIN_IN_AREA_EXPOSED, {
                    "domain": domain,
                    "area": constraints.area_name,
                }
            if constraints.floor_name:
                return ErrorKey.NO_DOMAIN_IN_FLOOR_EXPOSED, {
                    "domain": domain,
                    "floor": constraints.floor_name,
                }
            return ErrorKey.NO_DOMAIN_EXPOSED, {"domain": domain}

    if reason == MatchFailedReason.AREA:
        if constraints.states:
            # Entity is not in correct state
            assert constraints.states
            state = next(iter(constraints.states))

            return ErrorKey.ENTITY_WRONG_STATE, {"state": state}

        if constraints.features:
            # Feature not supported by entity
            return ErrorKey.FEATURE_NOT_SUPPORTED, {}

        if constraints.domains:
            domain = next(iter(constraints.domains))

            if constraints.area_name:
                return ErrorKey.NO_DOMAIN_IN_AREA_EXPOSED, {
                    "domain": domain,
                    "area": constraints.area_name,
                }
            if constraints.floor_name:
                return ErrorKey.NO_DOMAIN_IN_FLOOR_EXPOSED, {
                    "domain": domain,
                    "floor": constraints.floor_name,
                }
            return ErrorKey.NO_DOMAIN_EXPOSED, {"domain": domain}

    # Default error
    return ErrorKey.NO_INTENT, {}
