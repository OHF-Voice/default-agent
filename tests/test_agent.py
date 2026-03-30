"""Tests for default agent."""

from unittest.mock import Mock, patch

import pytest

from default_agent.agent import render_response
from default_agent.hass_api import InfoForRecognition


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

    info = InfoForRecognition(
        slot_lists={},
        preferred_area_id=None,
        preferred_area_name=None,
        preferred_floor_id=None,
        states={},
        entities={},
        areas={},
        floors={},
        satellite_devices={},
    )

    template = f"{{{{ num_to_words({num}, '{format_type}') }}}}"

    with patch.object(
        lang_intents, "intent_responses", {"TestIntent": {"default": template}}
    ):
        response = render_response(result, lang_intents, info)
        assert response == expected
