import itertools
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from .models import (
    ATTR_DEVICE_CLASS,
    ATTR_SUPPORTED_FEATURES,
    Area,
    Entity,
    Floor,
    State,
)


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


@dataclass
class MatchTargetsPreferences:
    """Preferences used to disambiguate duplicate name matches in async_match_targets."""

    area_id: str | None = None
    """Id of area to use when deduplicating names."""

    floor_id: str | None = None
    """Id of floor to use when deduplicating names."""


@dataclass
class MatchTargetsCandidate:
    """Candidate for async_match_targets."""

    state: State
    entity: Entity | None = None
    area: Area | None = None
    matched_name: str | None = None


@dataclass
class MatchTargetsResult:
    """Result from async_match_targets."""

    is_match: bool
    """True if one or more entities matched."""

    no_match_reason: MatchFailedReason | None = None
    """Reason for failed match when is_match = False."""

    states: List[State] = field(default_factory=list)
    """List of matched entity states."""

    no_match_name: str | None = None
    """Name of invalid area/floor or duplicate name when match fails for those reasons."""

    areas: List[Area] = field(default_factory=list)
    """Areas that were targeted."""

    floors: List[Floor] = field(default_factory=list)
    """Floors that were targeted."""


# -----------------------------------------------------------------------------


def _default_area_candidate_filter(
    candidate: MatchTargetsCandidate, possible_area_ids: Collection[str]
) -> bool:
    """Keep candidates in the possible areas."""
    return (candidate.area is not None) and (
        candidate.area.area_id in possible_area_ids
    )


def _normalize_name(name: str) -> str:
    """Normalize name for comparison."""
    return name.strip().casefold()


def _filter_by_name(
    name: str,
    candidates: Iterable[MatchTargetsCandidate],
) -> Iterable[MatchTargetsCandidate]:
    """Filter candidates by name."""
    name_norm = _normalize_name(name)

    for candidate in candidates:
        # Accept entity id
        if candidate.state.entity_id == name:
            candidate.matched_name = name
            yield candidate
            continue

        if candidate.entity is None:
            continue

        for candidate_name in candidate.entity.names:
            if _normalize_name(candidate_name) == name_norm:
                candidate.matched_name = name
                yield candidate
                break


def _filter_by_features(
    features: int,
    candidates: Iterable[MatchTargetsCandidate],
) -> Iterable[MatchTargetsCandidate]:
    """Filter candidates by supported features."""
    for candidate in candidates:
        if (candidate.entity is not None) and (
            (candidate.entity.supported_features & features) == features
        ):
            yield candidate
            continue

        supported_features = candidate.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if (supported_features & features) == features:
            yield candidate


def _filter_by_device_classes(
    device_classes: Iterable[str],
    candidates: Iterable[MatchTargetsCandidate],
) -> Iterable[MatchTargetsCandidate]:
    """Filter candidates by device classes."""
    for candidate in candidates:
        if (
            (candidate.entity is not None)
            and candidate.entity.device_class
            and (candidate.entity.device_class in device_classes)
        ):
            yield candidate
            continue

        device_class = candidate.state.attributes.get(ATTR_DEVICE_CLASS)
        if device_class and (device_class in device_classes):
            yield candidate


def find_areas(name: str, areas: Iterable[Area]) -> Iterable[Area]:
    """Find all areas matching a name (including aliases)."""
    name_norm = _normalize_name(name)
    for area in areas:
        # Accept name or area id
        if (area.area_id == name) or (_normalize_name(area.name) == name_norm):
            yield area
            continue

        if not area.aliases:
            continue

        for alias in area.aliases:
            if _normalize_name(alias) == name_norm:
                yield area
                break


def find_floors(name: str, floors: Iterable[Floor]) -> Iterable[Floor]:
    """Find all floors matching a name (including aliases)."""
    name_norm = _normalize_name(name)
    for floor in floors:
        # Accept name or floor id
        if (floor.floor_id == name) or (_normalize_name(floor.name) == name_norm):
            yield floor
            continue

        if not floor.aliases:
            continue

        for alias in floor.aliases:
            if _normalize_name(alias) == name_norm:
                yield floor
                break


# -----------------------------------------------------------------------------


def async_match_targets(
    states: List[State],
    *,
    entities: Dict[str, Entity],
    areas: Dict[str, Area],
    floors: Dict[str, Floor],
    constraints: MatchTargetsConstraints,
    preferences: MatchTargetsPreferences | None = None,
    area_candidate_filter: Callable[
        [MatchTargetsCandidate, Collection[str]], bool
    ] = _default_area_candidate_filter,
) -> MatchTargetsResult:
    """Match entities based on constraints in order to handle an intent."""
    preferences = preferences or MatchTargetsPreferences()

    if constraints.domains:
        states = [s for s in states if s.domain in constraints.domains]
        if not states:
            return MatchTargetsResult(False, MatchFailedReason.DOMAIN)

    if constraints.states:
        # Filter by state
        states = [s for s in states if s.state in constraints.states]
        if not states:
            return MatchTargetsResult(False, MatchFailedReason.STATE)

    candidates = []
    for state in states:
        candidate = MatchTargetsCandidate(state, entity=entities.get(state.entity_id))
        if (candidate.entity is not None) and candidate.entity.area_id:
            candidate.area = areas.get(candidate.entity.area_id)

        candidates.append(candidate)

    if constraints.name:
        # Filter by entity name or alias
        candidates = list(_filter_by_name(constraints.name, candidates))
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.NAME)

    if constraints.features:
        # Filter by supported features
        candidates = list(_filter_by_features(constraints.features, candidates))
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.FEATURE)

    if constraints.device_classes:
        # Filter by device class
        candidates = list(
            _filter_by_device_classes(constraints.device_classes, candidates)
        )
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.DEVICE_CLASS)

    # Check floor/area constraints
    targeted_floors: List[Floor] | None = None
    targeted_areas: List[Area] | None = None

    if constraints.floor_name or constraints.area_name:
        if constraints.floor_name:
            # Filter by areas associated with floor
            targeted_floors = list(find_floors(constraints.floor_name, floors.values()))
            if not targeted_floors:
                return MatchTargetsResult(
                    False,
                    MatchFailedReason.INVALID_FLOOR,
                    no_match_name=constraints.floor_name,
                )

            possible_floor_ids = {floor.floor_id for floor in targeted_floors}
            possible_area_ids = {
                area.area_id
                for area in areas.values()
                if area.floor_id in possible_floor_ids
            }

            candidates = [
                c for c in candidates if area_candidate_filter(c, possible_area_ids)
            ]
            if not candidates:
                return MatchTargetsResult(
                    False, MatchFailedReason.FLOOR, floors=targeted_floors
                )
        else:
            # All areas are possible
            possible_area_ids = set(areas.keys())

        if constraints.area_name:
            targeted_areas = list(find_areas(constraints.area_name, areas.values()))
            if not targeted_areas:
                return MatchTargetsResult(
                    False,
                    MatchFailedReason.INVALID_AREA,
                    no_match_name=constraints.area_name,
                )

            matching_area_ids = {area.area_id for area in targeted_areas}

            # May be constrained by floors above
            possible_area_ids.intersection_update(matching_area_ids)
            candidates = [
                c for c in candidates if area_candidate_filter(c, possible_area_ids)
            ]
            if not candidates:
                return MatchTargetsResult(
                    False, MatchFailedReason.AREA, areas=targeted_areas
                )

    if constraints.name and (not constraints.allow_duplicate_names):
        # Check for duplicates
        sorted_candidates = sorted(
            [c for c in candidates if c.matched_name],
            key=lambda c: c.matched_name or "",
        )
        final_candidates: List[MatchTargetsCandidate] = []
        for name, group in itertools.groupby(
            sorted_candidates, key=lambda c: c.matched_name
        ):
            group_candidates = list(group)
            if len(group_candidates) < 2:
                # No duplicates for name
                final_candidates.extend(group_candidates)
                continue

            # Try to disambiguate by preferences
            if preferences.floor_id:
                group_candidates = [
                    c
                    for c in group_candidates
                    if (c.area is not None)
                    and (c.area.floor_id == preferences.floor_id)
                ]
                if len(group_candidates) < 2:
                    # Disambiguated by floor
                    final_candidates.extend(group_candidates)
                    continue

            if preferences.area_id:
                group_candidates = [
                    c
                    for c in group_candidates
                    if area_candidate_filter(c, {preferences.area_id})
                ]
                if len(group_candidates) < 2:
                    # Disambiguated by area
                    final_candidates.extend(group_candidates)
                    continue

            # Couldn't disambiguate duplicate names
            return MatchTargetsResult(
                False,
                MatchFailedReason.DUPLICATE_NAME,
                no_match_name=name,
                areas=targeted_areas or [],
                floors=targeted_floors or [],
            )

        if not final_candidates:
            return MatchTargetsResult(
                False,
                MatchFailedReason.NAME,
                areas=targeted_areas or [],
                floors=targeted_floors or [],
            )

        candidates = final_candidates

    if constraints.single_target and len(candidates) > 1:
        # Find best match using preferences
        if not (preferences.area_id or preferences.floor_id):
            # No preferences
            return MatchTargetsResult(
                False,
                MatchFailedReason.MULTIPLE_TARGETS,
                states=[c.state for c in candidates],
            )

        filtered_candidates: List[MatchTargetsCandidate] = candidates
        if preferences.area_id:
            # Filter by area
            filtered_candidates = [
                c for c in candidates if area_candidate_filter(c, {preferences.area_id})
            ]

        if (len(filtered_candidates) > 1) and preferences.floor_id:
            # Filter by floor
            filtered_candidates = [
                c
                for c in candidates
                if c.area and (c.area.floor_id == preferences.floor_id)
            ]

        if len(filtered_candidates) != 1:
            # Filtering could not restrict to a single target
            return MatchTargetsResult(
                False,
                MatchFailedReason.MULTIPLE_TARGETS,
                states=[c.state for c in candidates],
            )

        # Filtering succeeded
        candidates = filtered_candidates

    return MatchTargetsResult(
        True,
        None,
        states=[c.state for c in candidates],
        areas=targeted_areas or [],
        floors=targeted_floors or [],
    )
