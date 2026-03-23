"""Default agent implementation."""

import itertools
import logging
from typing import Any, Dict, Optional, Tuple

from hassil import RecognizeResult, recognize_best
from home_assistant_intents import ErrorKey
from jinja2 import BaseLoader, Environment, StrictUndefined
from unicode_rbnf import FormatPurpose, RbnfEngine


from .const import SLOT_NAME, SLOT_AREA, SLOT_FLOOR, SLOT_DOMAIN
from .hass_api import HomeAssistant, InfoForRecognition
from .intents_loader import LanguageIntents
from .name_matcher import (
    MatchFailedReason,
    MatchTargetsConstraints,
    MatchTargetsPreferences,
    MatchTargetsResult,
    async_match_targets,
)
from .intents import async_handle_intent, IntentHandledResult

_LOGGER = logging.getLogger(__name__)

_DEFAULT_ERROR_TEXT = "Sorry, I couldn't understand that."
_ENV = Environment(loader=BaseLoader(), undefined=StrictUndefined)

# language -> engine
_RNBF_ENGINES: Dict[str, RbnfEngine] = {}


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
    intent_result = recognize_best(
        text,
        lang_intents.intents,
        slot_lists=hass_info.slot_lists,
        intent_context=intent_context,
        language=lang_intents.language,
        best_slot_name=SLOT_NAME,
    )  # TODO: prefer custom sentences with "best_metadata_key"
    if intent_result is None:
        # TODO: re-run with unmatched entities?
        _LOGGER.debug(
            "No intent recognized for text (language=%s): %s",
            lang_intents.language,
            text,
        )
        return (False, render_error(lang_intents, ErrorKey.NO_INTENT))

    _LOGGER.debug(
        "Recognized intent '%s' with slots: %s, context: %s",
        intent_result.intent.name,
        intent_result.entities,
        intent_result.context,
    )

    # Match names
    constraints = MatchTargetsConstraints()
    name_value = intent_result.entities.get(SLOT_NAME)
    if name_value is not None:
        constraints.name = name_value.value

    domain_value = intent_result.entities.get(SLOT_DOMAIN)
    if domain_value is not None:
        constraints.domains = {domain_value.value}

    preferences: Optional[MatchTargetsPreferences] = None
    if hass_info.preferred_area_id or hass_info.preferred_floor_id:
        preferences = MatchTargetsPreferences(
            area_id=hass_info.preferred_area_id, floor_id=hass_info.preferred_floor_id
        )

    _LOGGER.debug("Constaints: %s", constraints)
    _LOGGER.debug("Preferences: %s", preferences)

    match_result = async_match_targets(
        hass_info.states.values(),
        entities=hass_info.entities,
        areas=hass_info.areas,
        floors=hass_info.floors,
        constraints=constraints,
        preferences=preferences,
    )

    _LOGGER.debug("Match result: %s", match_result)

    if not match_result.is_match:
        error_key, error_data = get_match_error_response(match_result, constraints)
        error_text = render_error(lang_intents, error_key, error_data)
        return (False, error_text)

    handle_result = await async_handle_intent(hass, intent_result, match_result)
    if handle_result:
        response_text = render_response(
            intent_result, handle_result, lang_intents, hass_info
        )
        return (True, response_text)

    return (False, _DEFAULT_ERROR_TEXT)


def render_response(
    intent_result: RecognizeResult,
    handle_result: IntentHandledResult,
    lang_intents: LanguageIntents,
    info: InfoForRecognition,
) -> str:
    """Render the response Jinja2 template for the intent.

    This is done locally rather than in Home Assistant, so we need to patch
    things to keep the Jinja2 environment compatible with existing response
    templates.
    """
    # result.response is a key into the intent's response templates
    response_template = lang_intents.intent_responses.get(
        intent_result.intent.name, {}
    ).get(intent_result.response)
    if not response_template:
        # No response template
        return ""

    slots: Dict[str, Any] = {e.name: e.value for e in intent_result.entities_list}
    slots.update(handle_result.speech_slots)

    def state_attr(entity_id: str, attr_name: str) -> Any:
        state = info.states.get(entity_id)
        if state is None:
            return None

        return state.attributes.get(attr_name)

    variables: Dict[str, Any] = {"slots": slots, "state_attr": state_attr}

    # The "query" field is mainly used by HassGetState to tell which entities
    # matched the question.
    #
    # If the users asks "is the bedroom light on", its state will show up in
    # "matched" if it's state is "on" and in "unmatched" if it's not.
    query = {
        "matched": handle_result.matched_states,
        "unmatched": handle_result.unmatched_states,
    }

    variables["query"] = query
    if handle_result.matched_states is not None:
        # The first matched or unmatched entity is available as "state".
        variables["state"] = handle_result.matched_states[0]

    # Try to load engine for transforming numbers into words.
    number_engine = _RNBF_ENGINES.get(lang_intents.language)
    if number_engine is None:
        try:
            number_engine = RbnfEngine.for_language(lang_intents.language)
        except ValueError:
            _LOGGER.debug(
                "num_to_words() doesn't supported language '%s'", lang_intents.language
            )

    def num_to_words(number, purpose: str = "cardinal") -> str:
        if number_engine is None:
            # Not much else we can do
            return str(number)

        if purpose == "year":
            format_purpose = FormatPurpose.YEAR
        elif purpose == "ordinal":
            format_purpose = FormatPurpose.ORDINAL
        else:
            # Default
            format_purpose = FormatPurpose.CARDINAL

        return number_engine.format_number(number, purpose=format_purpose).text

    variables["num_to_words"] = num_to_words

    # TODO: We're using StrictUndefined for Jinja2 rendering right now.
    # We may want to consider making undefined objects "falsey" like Home
    # Assistant does.
    _LOGGER.debug(
        "Rendering response '%s' with variables %s: %s",
        intent_result.response,
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


def get_match_error_response(
    match_result: MatchTargetsResult, constraints: MatchTargetsConstraints
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

    reason = match_result.no_match_reason
    no_match_name = match_result.no_match_name

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
