from enum import Enum
from dataclasses import dataclass
from collections.abc import Collection
from typing import Any, Dict, Tuple

from home_assistant_intents import ErrorKey


class MatchFailedReason(str, Enum):
    DOMAIN = "DOMAIN"
    DEVICE_CLASS = "DEVICE_CLASS"
    STATE = "STATE"
    FEATURE = "FEATURE"
    ASSISTANT = "ASSISTANT"
    AREA = "AREA"
    DUPLICATE_NAME = "DUPLICATE_NAME"
    INVALID_AREA = "INVALID_AREA"
    INVALID_FLOOR = "INVALID_FLOOR"


@dataclass
class MatchTargetsConstraints:
    """Constraints for async_match_targets."""

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


def get_match_error_response(
    match_error: Dict[str, Any],
) -> Tuple[ErrorKey, Dict[str, Any]]:
    """Return key and template arguments for error when target matching fails."""

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
