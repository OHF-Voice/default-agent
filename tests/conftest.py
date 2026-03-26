from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import partial
from typing import Any, Dict, Tuple
from unittest.mock import AsyncMock

import pytest
from hassil import SlotList, TextSlotList

from default_agent.agent import async_converse as agent_async_converse
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
    current_floor = Floor("current-floor", "Current Floor")
    current_area = Area("current-area", "Current Area", floor_id=current_floor.floor_id)
    other_area = Area("other-area", "Other Area")

    light_current_area = Entity(
        "light.light_current_area", "Light Current Area", area_id=current_area.area_id
    )
    light_other_area = Entity(
        "light.light_other_area", "Light Other Area", area_id=other_area.area_id
    )

    floors = [current_floor]
    areas = [current_area, other_area]
    entities = [light_current_area, light_other_area]
    states = [to_state(light_current_area, "on")]

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
        preferred_floor_id=current_floor.floor_id,
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
