"""Tests for built-in intent handlers."""

from collections.abc import Awaitable, Callable
from functools import partial
from typing import Dict, Tuple, Any
from unittest.mock import AsyncMock, patch

import pytest
from hassil import SlotList, TextSlotList

from default_agent.agent import async_converse as agent_async_converse
from default_agent.hass_api import InfoForRecognition
from default_agent.models import Area, Floor, Entity, State
from default_agent.intents_loader import IntentsLoader

from .conftest import TEST_DATETIME

CONVERSE_TYPE = Callable[[str], Awaitable[Tuple[bool, str]]]


def to_state(entity: Entity, state: Any) -> State:
    return State(
        entity.entity_id, state, attributes=entity.attributes, entity_name=entity.name
    )


@pytest.fixture(name="async_converse", scope="session")
def async_converse_fixture() -> CONVERSE_TYPE:
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

    hass_info = InfoForRecognition(
        slot_lists=slot_lists,
        preferred_area_id=current_area.area_id,
        preferred_area_name=current_area.name,
        preferred_floor_id=current_floor.floor_id,
        states={s.entity_id: s for s in states},
        entities={e.entity_id: e for e in entities},
        areas={a.area_id: a for a in areas},
        floors={f.floor_id: f for f in floors},
    )
    hass = AsyncMock()
    hass.get_info.return_value = hass_info

    intents_loader = IntentsLoader()
    lang_intents = intents_loader.get_intents("en")
    assert lang_intents is not None, "No English intents"

    return partial(
        agent_async_converse,
        hass=hass,
        lang_intents=lang_intents,
        intent_handlers=intents_loader.get_intent_handlers(),
    )


@pytest.mark.asyncio
async def test_get_time(async_converse: CONVERSE_TYPE):
    """Test HassGetCurrentTime intent."""
    with patch("default_agent.intents.get_current_time.datetime") as mock_datetime:
        mock_datetime.now.return_value = TEST_DATETIME
        success, response = await async_converse("what time is it")
    assert success, "Intent recognition failed"
    assert response == "1:02 AM"


@pytest.mark.asyncio
async def test_get_date(async_converse: CONVERSE_TYPE):
    """Test HassGetCurrentDate intent."""
    with patch("default_agent.intents.get_current_date.datetime") as mock_datetime:
        mock_datetime.now.return_value = TEST_DATETIME
        success, response = await async_converse("what's the date")
    assert success, "Intent recognition failed"
    assert response == "September 17th, 2013"


@pytest.mark.asyncio
async def test_turn_on_lights_current_area(async_converse: CONVERSE_TYPE):
    """Test HassTurnOn intent with lights in the current area."""
    success, response = await async_converse("turn on the lights")
    assert success, "Intent recognition failed"
    assert response == "Turned on the lights"
