from typing import Dict, List

from default_agent.models import Entity, Area, Floor, State
from default_agent.name_matcher import (
    async_match_targets,
    MatchFailedReason,
    MatchTargetsConstraints,
    MatchTargetsPreferences,
)


async def test_async_match_targets() -> None:
    """Tests for async_match_targets function."""
    # House layout
    # Floor 1 (ground):
    #   - Kitchen
    #     - Outlet
    #   - Bathroom
    #     - Light
    # Floor 2 (upstairs)
    #   - Bedroom
    #     - Switch
    #   - Bathroom
    #     - Light
    # Floor 3 (also upstairs)
    #   - Bedroom
    #     - Switch
    #   - Bathroom
    #     - Light

    # Floor 1
    floor_1 = Floor(floor_id="first_floor", name="first floor", aliases=["ground"])
    area_kitchen = Area(area_id="kitchen", name="kitchen", floor_id=floor_1.floor_id)

    area_bathroom_1 = Area(
        area_id="first_floor_bathroom",
        name="first floor bathroom",
        aliases=["bathroom"],
        floor_id=floor_1.floor_id,
    )

    kitchen_outlet = Entity(
        entity_id="switch.kitchen_outlet",
        name="kitchen outlet",
        aliases=["kitchen outlet"],
        area_id=area_kitchen.area_id,
        attributes={"device_class": "outlet"},
    )
    state_kitchen_outlet = State(entity_id=kitchen_outlet.entity_id, state="on")

    bathroom_light_1 = Entity(
        entity_id="light.bathroom_light_1",
        name="bathroom light",
        aliases=["bathroom light", "overhead light"],
        area_id=area_bathroom_1.area_id,
    )
    state_bathroom_light_1 = State(entity_id=bathroom_light_1.entity_id, state="off")

    # Floor 2
    floor_2 = Floor(floor_id="second_floor", name="second floor", aliases=["upstairs"])
    area_bedroom_2 = Area(
        area_id="second_floor_bedroom",
        name="second floor bedroom",
        floor_id=floor_2.floor_id,
    )
    area_bathroom_2 = Area(
        area_id="second_floor_bathroom",
        name="second floor bathroom",
        aliases=["bathroom"],
        floor_id=floor_2.floor_id,
    )

    bedroom_switch_2 = Entity(
        entity_id="switch.bedroom_switch_2",
        name="second floor bedroom switch",
        aliases=["second floor bedroom switch"],
        area_id=area_bedroom_2.area_id,
    )
    state_bedroom_switch_2 = State(entity_id=bedroom_switch_2.entity_id, state="off")

    bathroom_light_2 = Entity(
        entity_id="light.bathroom_light_2",
        name="bathroom light",
        aliases=["bathroom light", "overhead light"],
        area_id=area_bathroom_2.area_id,
        attributes={"supported_features": 1},
    )
    state_bathroom_light_2 = State(entity_id=bathroom_light_2.entity_id, state="off")

    # Floor 3
    floor_3 = Floor(floor_id="third_floor", name="third floor", aliases=["upstairs"])
    area_bedroom_3 = Area(
        area_id="third_floor_bedroom",
        name="third floor bedroom",
        floor_id=floor_3.floor_id,
    )
    area_bathroom_3 = Area(
        area_id="third_floor_bathroom",
        name="third floor bathroom",
        aliases=["bathroom"],
        floor_id=floor_3.floor_id,
    )

    bedroom_switch_3 = Entity(
        entity_id="switch.bedroom_switch_3",
        name="third floor bedroom switch",
        aliases=["third floor bedroom switch"],
        area_id=area_bedroom_3.area_id,
        attributes={"device_class": "outlet"},
    )
    state_bedroom_switch_3 = State(
        entity_id=bedroom_switch_3.entity_id,
        state="off",
        attributes={"device_class": "outlet"},
    )

    bathroom_light_3 = Entity(
        entity_id="light.bathroom_light_3",
        name="overhead light",
        aliases=["overhead light", "bathroom light"],
        area_id=area_bathroom_3.area_id,
        attributes={"supported_features": 1, "friendly_name": "bathroom light"},
    )
    state_bathroom_light_3 = State(
        entity_id=bathroom_light_3.entity_id,
        state="on",
        attributes={"supported_features": 1},
    )

    # -----
    entities: Dict[str, Entity] = {
        e.entity_id: e
        for e in (
            kitchen_outlet,
            bathroom_light_1,
            bathroom_light_2,
            bathroom_light_3,
            bedroom_switch_2,
            bedroom_switch_3,
        )
    }
    areas: Dict[str, Area] = {
        a.area_id: a
        for a in (
            area_kitchen,
            area_bathroom_1,
            area_bathroom_2,
            area_bathroom_3,
            area_bedroom_2,
            area_bedroom_3,
        )
    }
    floors: Dict[str, Floor] = {f.floor_id: f for f in (floor_1, floor_2, floor_3)}

    bathroom_light_states = [
        state_bathroom_light_1,
        state_bathroom_light_2,
        state_bathroom_light_3,
    ]
    states: List[State] = [
        *bathroom_light_states,
        state_kitchen_outlet,
        state_bedroom_switch_2,
        state_bedroom_switch_3,
    ]

    # -----
    # Not a unique name
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light"),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == MatchFailedReason.DUPLICATE_NAME
    assert result.no_match_name == "bathroom light"

    # Works with duplicate names allowed
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light", allow_duplicate_names=True),
        states=states,
    )
    assert result.is_match
    assert {s.entity_id for s in result.states} == {
        s.entity_id for s in bathroom_light_states
    }

    # Also works when name is not a constraint
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(domains={"light"}),
        states=states,
    )
    assert result.is_match
    assert {s.entity_id for s in result.states} == {
        s.entity_id for s in bathroom_light_states
    }

    # We can disambiguate by preferred floor (from context)
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light"),
        MatchTargetsPreferences(floor_id=floor_3.floor_id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_3.entity_id

    # Also disambiguate by preferred area (from context)
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light"),
        MatchTargetsPreferences(area_id=area_bathroom_2.area_id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_2.entity_id

    # Disambiguate by floor name, if unique
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light", floor_name="ground"),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Doesn't work if floor name/alias is not unique
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light", floor_name="upstairs"),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == MatchFailedReason.DUPLICATE_NAME

    # Disambiguate by area name, if unique
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(
            name="bathroom light", area_name="first floor bathroom"
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Doesn't work if area name/alias is not unique
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(name="bathroom light", area_name="bathroom"),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == MatchFailedReason.DUPLICATE_NAME

    # Does work if floor/area name combo is unique
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(
            name="bathroom light", area_name="bathroom", floor_name="ground"
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Doesn't work if area is not part of the floor
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(
            name="bathroom light",
            area_name="second floor bathroom",
            floor_name="ground",
        ),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == MatchFailedReason.AREA

    # Check state constraint (only third floor bathroom light is on)
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(domains={"light"}, states={"on"}),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_3.entity_id

    result = async_match_targets(
        hass,
        MatchTargetsConstraints(domains={"light"}, states={"on"}, floor_name="ground"),
        states=states,
    )
    assert not result.is_match

    # Check assistant constraint (exposure)
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(assistant="test"),
        states=states,
    )
    assert not result.is_match

    async_expose_entity(hass, "test", bathroom_light_1.entity_id, True)
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(assistant="test"),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Check device class constraint
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(
            domains={"switch"}, device_classes={switch.SwitchDeviceClass.OUTLET}
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 2
    assert {s.entity_id for s in result.states} == {
        kitchen_outlet.entity_id,
        bedroom_switch_3.entity_id,
    }

    # Check features constraint (second and third floor bathroom lights have effects)
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(
            domains={"light"}, features=light.LightEntityFeature.EFFECT
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 2
    assert {s.entity_id for s in result.states} == {
        bathroom_light_2.entity_id,
        bathroom_light_3.entity_id,
    }

    # Check single target constraint
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(domains={"light"}, single_target=True),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == MatchFailedReason.MULTIPLE_TARGETS

    # Only one light on the ground floor
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(domains={"light"}, single_target=True),
        preferences=MatchTargetsPreferences(floor_id=floor_1.floor_id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Only one switch in bedroom
    result = async_match_targets(
        hass,
        MatchTargetsConstraints(domains={"switch"}, single_target=True),
        preferences=MatchTargetsPreferences(area_id=area_bedroom_2.area_id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bedroom_switch_2.entity_id
