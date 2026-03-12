"""Tests for Home Assistant API."""

from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hassil import TextSlotList

from default_agent.hass_api import HomeAssistant


class MockWebsocket:
    """Mock websocket responses from Home Assistant server."""

    def __init__(
        self,
        responses: List[
            Union[
                Tuple[Optional[str], Dict[str, Any]],
                Tuple[Optional[str], Dict[str, Any], Dict[str, Any]],
            ]
        ],
    ) -> None:
        # list of (type, response) tuples
        self.responses = responses

        self._next_msg: Optional[Dict[str, Any]] = None

    async def receive_json(self) -> Dict[str, Any]:
        """Get next response message."""
        assert self.responses

        response = self.responses[0]
        expected_msg: Optional[Dict[str, Any]] = None

        if len(response) == 3:
            response_type, response_data, expected_msg = response
        else:
            response_type, response_data = response

        if response_type:
            assert self._next_msg
            assert response_type == self._next_msg["type"]

        if expected_msg:
            assert self._next_msg
            for key, value in expected_msg.items():
                assert key in self._next_msg
                assert self._next_msg[key] == value

        self.responses = self.responses[1:]
        self._next_msg = None

        response_data["success"] = True
        return response_data

    async def send_json(self, msg):
        """Set type of next command."""
        self._next_msg = msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


def _make_session(mock_websocket: MockWebsocket) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.ws_connect = MagicMock(return_value=mock_websocket)

    return mock_session


@pytest.mark.asyncio
async def test_unexposed_and_disabled_entities() -> None:
    """Test that unexposed and disabled entities are skipped."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "light.unexposed_light": {"conversation": False},
                            "light.disabled_light": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {"entity_id": "light.unexposed_light"},
                        {
                            "entity_id": "light.disabled_light",
                        },
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "light.disabled_light": {
                            "name": "Disabled Light",
                            "disabled_by": {},
                        },
                    }
                },
                {"entity_ids": ["light.disabled_light"]},
            ),
            ("config/device_registry/list", {"result": []}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await HomeAssistant("<token>").get_info()
        name_list = ha_info.slot_lists.get("name")
        assert isinstance(name_list, TextSlotList)
        assert not name_list.values
