"""Tests for default agent."""

from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest
from hassil import SlotList, TextSlotList

from default_agent.agent import async_converse, render_response
from default_agent.hass_api import InfoForRecognition
from default_agent.intents_loader import IntentsLoader

_TEST_DATETIME = datetime(year=2013, month=9, day=17, hour=1, minute=2)


@pytest.fixture(name="intents_loader", scope="session")
def intents_loader_fixture() -> IntentsLoader:
    """Intents loader."""
    return IntentsLoader()


@pytest.fixture(name="slot_lists", scope="session")
def slot_lists_fixture() -> Dict[str, SlotList]:
    """Empty name/area/floor slot lists for built-in templates."""
    return {
        "name": TextSlotList(name="name", values=[]),
        "area": TextSlotList(name="area", values=[]),
        "floor": TextSlotList(name="floor", values=[]),
    }


@pytest.mark.asyncio
async def test_async_converse(
    intents_loader: IntentsLoader, slot_lists: Dict[str, SlotList]
):
    """Test basic intent recognition and response rendering."""
    lang_intents = intents_loader.get_intents("en")
    assert lang_intents is not None

    hass_info = InfoForRecognition(
        slot_lists=slot_lists,
        preferred_area_id="test-area",
        preferred_area_name="Test Area",
        preferred_floor_id="test-floor",
        entity_attributes={},
    )
    hass = AsyncMock()
    hass.get_info.return_value = hass_info
    hass.handle_intent.return_value = {
        "response_type": "query_answer",
        "speech_slots": {"time": _TEST_DATETIME.time().isoformat()},
    }

    success, response = await async_converse(hass, "what time is it", lang_intents)
    assert success, "Intent recognition failed"
    assert response == "1:02 AM"


@pytest.mark.asyncio
async def test_async_converse_error(
    intents_loader: IntentsLoader, slot_lists: Dict[str, SlotList]
):
    """Test error message from async_converse."""
    lang_intents = intents_loader.get_intents("en")
    assert lang_intents is not None

    hass_info = InfoForRecognition(
        slot_lists=slot_lists,
        preferred_area_id="test-area",
        preferred_area_name="Test Area",
        preferred_floor_id="test-floor",
        entity_attributes={},
    )
    hass = AsyncMock()
    hass.get_info.return_value = hass_info
    hass.handle_intent.return_value = {
        "response_type": "error",
        "data": {
            "match_error": {
                "no_match_reason": "DOMAIN",
                "constraints": {"domains": ["light"]},
            }
        },
    }

    success, response = await async_converse(hass, "turn on the lights", lang_intents)
    assert not success
    assert response == "Sorry, I am not aware of any light"


@pytest.mark.parametrize(
    "num,format_type,expected",
    [
        (2020, "year", "twenty twenty"),
        (1, "ordinal", "first"),
        (42, "cardinal", "forty-two"),
    ],
)
def test_num_to_words(num: int, format_type: str, expected: str) -> None:
    """Test the num_to_words() function available in response templates."""
    lang_intents = Mock()
    lang_intents.language = "en"

    result = Mock()
    result.intent.name = "TestIntent"
    result.response = "default"
    result.entities_list = []

    info = Mock()
    intent_response: Dict[str, Any] = {}

    template = f"{{{{ num_to_words({num}, '{format_type}') }}}}"

    with patch.object(
        lang_intents, "intent_responses", {"TestIntent": {"default": template}}
    ):
        response = render_response(result, intent_response, lang_intents, info)
        assert response == expected
