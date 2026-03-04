"""Tests for intent loader."""

from pathlib import Path
from typing import Dict

import pytest
from hassil import SlotList, TextSlotList, recognize

from default_agent.intents_loader import IntentsLoader

_TESTS_DIR = Path(__file__).parent


@pytest.fixture
def intents_loader_fixture(name="intents_loader", scope="session") -> IntentsLoader:
    """Intents loader with custom sentences."""
    custom_sentences_dir = _TESTS_DIR / "custom_sentences"
    return IntentsLoader(custom_sentences_dirs=[custom_sentences_dir])


@pytest.fixture
def slot_lists_fixture(name="slot_lists", scope="session") -> Dict[str, SlotList]:
    """Empty name/area/floor slot lists for built-in templates."""
    return {
        "name": TextSlotList(name="name", values=[]),
        "area": TextSlotList(name="area", values=[]),
        "floor": TextSlotList(name="floor", values=[]),
    }


def test_load_custom_intent(
    intents_loader: IntentsLoader, slot_lists: Dict[str, SlotList]
) -> None:
    lang_intents = intents_loader.get_intents("en")

    assert lang_intents is not None
    assert lang_intents.language == "en"

    # Custom intent is recognized
    result = recognize("this is test 5", lang_intents.intents, slot_lists=slot_lists)
    assert result is not None
    assert result.intent.name == "TestIntent"
    assert "number" in result.entities
    assert result.entities["number"].value == 5

    # Other intents are still available
    result = recognize("what time is it", lang_intents.intents, slot_lists=slot_lists)
    assert result is not None
    assert result.intent.name == "HassGetCurrentTime"
