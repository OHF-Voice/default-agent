"""Wrapper for Home Assistant REST/Websocket API."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

import aiohttp
from hassil import RecognizeResult
from hassil.expression import TextChunk
from hassil.intents import SlotList, TextSlotList, TextSlotValue

from .models import ATTR_FRIENDLY_NAME, Area, Entity, Floor, State

_LOGGER = logging.getLogger(__name__)


@dataclass
class InfoForRecognition:
    """Information gathered from Home Assistant for intent recognition."""

    slot_lists: Dict[str, SlotList]
    preferred_area_id: Optional[str]
    preferred_area_name: Optional[str]
    preferred_floor_id: Optional[str]
    states: Dict[str, State]
    entities: Dict[str, Entity]
    areas: Dict[str, Area]
    floors: Dict[str, Floor]


class HomeAssistant:
    """API to Home Assistant."""

    def __init__(
        self,
        token: str,
        api_url: str = "ws://homeassistant.local:8123/api/websocket",
    ) -> None:
        self.token = token
        if api_url.endswith("/"):
            api_url = api_url[:-1]

        self.api_url = api_url
        self.websocket_api_url = f"{api_url}/websocket"

    async def get_info(
        self, device_id: Optional[str] = None, satellite_id: Optional[str] = None
    ) -> InfoForRecognition:
        """Get necessary information for intent recognition."""
        current_id = 0

        def next_id() -> int:
            nonlocal current_id
            current_id += 1
            return current_id

        name_list = TextSlotList(name="name", values=[])
        area_names: Set[str] = set()
        floor_names: Set[str] = set()
        states: Dict[str, State] = {}
        entities: Dict[str, Entity] = {}
        areas: Dict[str, Area] = {}
        floors: Dict[str, Floor] = {}
        preferred_area_id: Optional[str] = None
        preferred_area_name: Optional[str] = None
        preferred_floor_id: Optional[str] = None

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                self.websocket_api_url, max_msg_size=0
            ) as websocket:
                # Authenticate
                msg = await websocket.receive_json()
                assert msg["type"] == "auth_required", msg

                await websocket.send_json(
                    {
                        "type": "auth",
                        "access_token": self.token,
                    },
                )

                msg = await websocket.receive_json()
                assert msg["type"] == "auth_ok", msg

                # Get exposed entities
                await websocket.send_json(
                    {"id": next_id(), "type": "homeassistant/expose_entity/list"}
                )

                msg = await websocket.receive_json()
                assert msg["success"], msg

                entity_ids = []
                for entity_id, exposed_info in msg["result"][
                    "exposed_entities"
                ].items():
                    if exposed_info.get("conversation"):
                        entity_ids.append(entity_id)

                await websocket.send_json(
                    {
                        "id": next_id(),
                        "type": "get_states",
                    }
                )
                msg = await websocket.receive_json()
                assert msg["success"], msg
                for state_data in msg["result"]:
                    states[state_data["entity_id"]] = State(
                        entity_id=state_data["entity_id"],
                        state=state_data["state"],
                        attributes=state_data.get("attributes", {}),
                    )

                # Floors
                await websocket.send_json(
                    {"id": next_id(), "type": "config/floor_registry/list"}
                )
                msg = await websocket.receive_json()
                assert msg["success"], msg
                for floor_data in msg["result"]:
                    floor_id = floor_data["floor_id"]
                    floors[floor_id] = Floor(
                        floor_id=floor_id,
                        name=floor_data["name"],
                        aliases=floor_data.get("aliases"),
                    )
                    names = [floor_data["name"]]
                    if floor_data.get("aliases"):
                        names.extend(floor_data["aliases"])
                    for name in names:
                        name = name.strip()
                        if name:
                            floor_names.add(name)

                # Areas
                await websocket.send_json(
                    {"id": next_id(), "type": "config/area_registry/list"}
                )
                msg = await websocket.receive_json()
                assert msg["success"], msg
                for area_data in msg["result"]:
                    area_id = area_data["area_id"]
                    areas[area_id] = Area(
                        area_id=area_id,
                        name=area_data["name"],
                        aliases=area_data.get("aliases"),
                        floor_id=area_data.get("floor_id"),
                    )
                    names = [area_data["name"]]
                    if area_data.get("aliases"):
                        names.extend(area_data["aliases"])
                    for name in names:
                        name = name.strip()
                        if name:
                            area_names.add(name)

                # Contains aliases
                # Check area_id as well as area of device_id
                # Use original_device_class
                await websocket.send_json(
                    {
                        "id": next_id(),
                        "type": "config/entity_registry/get_entries",
                        "entity_ids": entity_ids,
                    }
                )

                msg = await websocket.receive_json()
                assert msg["success"], msg
                for entity_id, entity_info in msg["result"].items():
                    domain = entity_id.split(".")[0]
                    name = None
                    names = []

                    if entity_info:
                        if entity_info.get("disabled_by") is not None:
                            # Skip disabled entities
                            continue

                        name = (
                            entity_info.get("name", "") or entity_info["original_name"]
                        )
                        if entity_info.get("aliases"):
                            names.extend(filter(None, entity_info["aliases"]))

                    entity_area_id = None
                    if entity_info:
                        entity_area_id = entity_info.get("area_id")

                    attributes: Dict[str, Any] = {}
                    state_data = states.get(entity_id)
                    if state_data:
                        attributes = state_data.attributes

                    if not name:
                        # Try friendly name
                        name = attributes.get(ATTR_FRIENDLY_NAME, "")

                    if name:
                        names.append(name)

                    entities[entity_id] = Entity(
                        entity_id=entity_id,
                        name=name,
                        aliases=names if names else None,
                        attributes=attributes,
                        area_id=entity_area_id,
                    )

                    for name in names:
                        name = name.strip()
                        if name:
                            name_list.values.append(
                                TextSlotValue(TextChunk(name), name, {"domain": domain})
                            )

                # Get device info
                await websocket.send_json(
                    {"id": next_id(), "type": "config/device_registry/list"}
                )
                msg = await websocket.receive_json()
                assert msg["success"], msg
                devices = {
                    device_info["id"]: device_info for device_info in msg["result"]
                }

                # Get preferred area
                if satellite_id:
                    # Get area of assist_satellite entity
                    await websocket.send_json(
                        {
                            "id": next_id(),
                            "type": "config/entity_registry/get_entries",
                            "entity_ids": [satellite_id],
                        }
                    )
                    msg = await websocket.receive_json()
                    assert msg["success"], msg
                    satellite_info = next(iter(msg["result"].values()))
                    satellite_area_id = satellite_info.get("area_id")
                    if satellite_area_id:
                        preferred_area_id = satellite_area_id
                    else:
                        # Use device area
                        satellite_device_id = satellite_info.get("device_id")
                        if satellite_device_id:
                            preferred_area_id = devices.get(
                                satellite_device_id, {}
                            ).get("area_id")
                elif device_id:
                    # Get area from device instead
                    preferred_area_id = devices.get(device_id, {}).get("area_id")

                if preferred_area_id:
                    preferred_area_info = areas.get(preferred_area_id)
                    if preferred_area_info:
                        preferred_area_name = preferred_area_info.name
                        preferred_floor_id = preferred_area_info.floor_id

        return InfoForRecognition(
            slot_lists={
                "name": name_list,
                "area": TextSlotList.from_strings(area_names, allow_template=False),
                "floor": TextSlotList.from_strings(floor_names, allow_template=False),
            },
            preferred_area_id=preferred_area_id,
            preferred_area_name=preferred_area_name,
            preferred_floor_id=preferred_floor_id,
            states=states,
            entities=entities,
            areas=areas,
            floors=floors,
        )

    async def handle_intent(
        self,
        result: RecognizeResult,
        language: str,
        *,
        device_id: Optional[str] = None,
        satellite_id: Optional[str] = None,
        assistant: Optional[str] = "conversation",
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle intent with REST API and return response."""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {e.name: e.value for e in result.entities_list}
        if extra_data:
            data.update(extra_data)

        _LOGGER.debug("Handling intent %s with: %s", result.intent.name, data)

        async with aiohttp.ClientSession() as session:
            web_response = await session.post(
                f"{self.api_url}/intent/handle",
                json={
                    "name": result.intent.name,
                    "data": data,
                    "language": language,
                    "assistant": assistant,
                    "device_id": device_id,
                    "satellite_id": satellite_id,
                },
                headers=headers,
            )
            assert web_response.status == 200
            return await web_response.json()
