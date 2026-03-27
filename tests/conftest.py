from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import partial
from typing import Any, Dict, Tuple
from unittest.mock import AsyncMock

import pytest
from hassil import SlotList, TextSlotList

from default_agent.agent import async_converse as agent_async_converse
from default_agent.const import (
    ClimateEntityFeature,
    FanEntityFeature,
    MediaPlayerEntityFeature,
    VacuumEntityFeature,
)
from default_agent.hass_api import InfoForRecognition
from default_agent.intents_loader import IntentsLoader
from default_agent.models import Area, Entity, Floor, LanguageIntents, State

TEST_DATETIME = datetime(year=2013, month=9, day=17, hour=1, minute=2)


def to_state(entity: Entity, state: Any) -> State:
    return State(
        entity.entity_id, state, attributes=entity.attributes, entity_name=entity.name
    )


@pytest.fixture(name="hass_info", scope="session")
def hass_info_fixture() -> InfoForRecognition:
    first_floor = Floor("first-floor", "First Floor")
    current_area = Area("current-area", "Current Area", floor_id=first_floor.floor_id)
    other_area = Area("other-area", "Other Area", floor_id=first_floor.floor_id)

    light_current_area = Entity(
        "light.current_light", "Current Light", area_id=current_area.area_id
    )
    switch_current_area = Entity(
        "switch.current_light", "Current Switch", area_id=current_area.area_id
    )
    light_other_area = Entity(
        "light.other_light", "Other Light", area_id=other_area.area_id
    )
    switch_other_area = Entity(
        "switch.other_switch", "Other Switch", area_id=other_area.area_id
    )
    light_no_area = Entity("light.no_area_light", "No Area Light")
    switch_no_area = Entity("switch.no_area_switch", "No Area Switch")
    climate_thermostat = Entity(
        "climate.thermostat",
        "Thermostat",
        area_id=current_area.area_id,
        attributes={"supported_features": ClimateEntityFeature.TARGET_TEMPERATURE},
    )
    fan_current = Entity(
        "fan.current_fan",
        "Smart Fan",
        area_id=current_area.area_id,
        attributes={"supported_features": FanEntityFeature.SET_SPEED},
    )
    media_player_tv = Entity(
        "media_player.tv",
        "TV",
        area_id=current_area.area_id,
        attributes={
            "supported_features": MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.VOLUME_SET,
            "volume_level": 0.5,
        },
    )
    media_player_stereo = Entity(
        "media_player.stereo",
        "Stereo",
        area_id=current_area.area_id,
        attributes={
            "supported_features": MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.VOLUME_MUTE
        },
    )
    vacuum_current = Entity(
        "vacuum.current_vacuum",
        "Smart Vacuum",
        area_id=current_area.area_id,
        attributes={
            "supported_features": VacuumEntityFeature.START
            | VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.CLEAN_AREA
        },
    )
    window_current = Entity(
        "cover.current_window",
        "Smart Window",
        area_id=current_area.area_id,
    )
    weather_home = Entity(
        "weather.home",
        "Home Weather",
        attributes={"temperature": 72, "temperature_unit": "F"},
    )
    todo_list = Entity("todo.list", "Todo List")

    floors = [first_floor]
    areas = [current_area, other_area]
    entities = [
        light_current_area,
        light_other_area,
        light_no_area,
        climate_thermostat,
        fan_current,
        media_player_tv,
        media_player_stereo,
        vacuum_current,
        window_current,
        weather_home,
        todo_list,
    ]
    states = [
        to_state(light_current_area, "on"),
        to_state(light_other_area, "off"),
        to_state(light_no_area, "on"),
        to_state(switch_current_area, "on"),
        to_state(switch_other_area, "off"),
        to_state(switch_no_area, "on"),
        to_state(climate_thermostat, "auto"),
        to_state(fan_current, "on"),
        to_state(media_player_tv, "playing"),
        to_state(media_player_stereo, "playing"),
        to_state(vacuum_current, "cleaning"),
        to_state(window_current, "closed"),
        to_state(weather_home, "sunny"),
        to_state(todo_list, ""),
    ]

    slot_lists: Dict[str, SlotList] = {
        "name": TextSlotList.from_tuples(
            ((e.name, e.name, {"domain": e.domain}) for e in entities),
            allow_template=False,
            name="name",
        ),
        "area": TextSlotList.from_strings(
            (a.name for a in areas), allow_template=False, name="area"
        ),
        "floor": TextSlotList.from_strings(
            (f.name for f in floors), allow_template=False, name="floor"
        ),
    }

    return InfoForRecognition(
        slot_lists=slot_lists,
        preferred_area_id=current_area.area_id,
        preferred_area_name=current_area.name,
        preferred_floor_id=first_floor.floor_id,
        states={s.entity_id: s for s in states},
        entities={e.entity_id: e for e in entities},
        areas={a.area_id: a for a in areas},
        floors={f.floor_id: f for f in floors},
    )


@pytest.fixture(name="intents_loader", scope="session")
def intents_loader_fixture() -> IntentsLoader:
    return IntentsLoader()


@pytest.fixture(name="lang_intents", scope="session")
def lang_intents_fixture(intents_loader: IntentsLoader) -> LanguageIntents:
    lang_intents = intents_loader.get_intents("en")
    assert lang_intents is not None, "No English intents"
    return lang_intents


@pytest.fixture(name="hass")
def hass_fixture(hass_info: InfoForRecognition) -> Any:

    hass = AsyncMock()
    hass.get_info.return_value = hass_info
    return hass


@pytest.fixture(name="async_converse")
def async_converse_fixture(
    hass: Any, lang_intents: LanguageIntents, intents_loader: IntentsLoader
) -> Callable[[str], Awaitable[Tuple[bool, str]]]:
    return partial(
        agent_async_converse,
        hass=hass,
        lang_intents=lang_intents,
        intent_handlers=intents_loader.get_intent_handlers(),
    )
