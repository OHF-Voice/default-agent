import argparse
import asyncio
import logging
from functools import partial
from importlib.metadata import version
from typing import Optional

from home_assistant_intents import get_languages
from jinja2 import BaseLoader, Environment, StrictUndefined
from wyoming.asr import Transcript
from wyoming.event import Event
from wyoming.handle import Handled, NotHandled
from wyoming.info import Attribution, Describe, HandleModel, HandleProgram, Info
from wyoming.server import AsyncEventHandler, AsyncServer

from .agent import async_converse
from .hass_api import HomeAssistant
from .intents_loader import IntentsLoader

_LOGGER = logging.getLogger(__name__)

_ERROR_NO_COMMAND = "Sorry, no command was given."
_ERROR_LANGUAGE_NOT_SUPPORTED = "Sorry, the language {language} is not supported."


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hass-token", required=True, help="Long-lived access token for Home Assistant"
    )
    parser.add_argument(
        "--hass-api",
        default="http://homeassistant.local:8123/api",
        help="URL of Home Assistant API",
    )
    parser.add_argument("--uri", default="stdio://", help="unix:// or tcp://")
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to log"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    _LOGGER.debug(args)

    hass = HomeAssistant(token=args.hass_token, api_url=args.hass_api)
    loader = IntentsLoader()

    server = AsyncServer.from_uri(args.uri)
    print("Ready")
    await server.run(partial(EventHandler, hass, loader, args))


class EventHandler(AsyncEventHandler):
    def __init__(
        self,
        hass: HomeAssistant,
        loader: IntentsLoader,
        cli_args: argparse.Namespace,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.hass = hass
        self.loader = loader
        self.args = cli_args
        self.env = Environment(loader=BaseLoader(), undefined=StrictUndefined)

    async def handle_event(self, event: Event) -> bool:
        try:
            return await self._handle_event(event)
        except Exception:
            _LOGGER.exception("Unexpected error handling event: %s", event)

        return False

    async def _handle_event(self, event: Event) -> bool:
        if Transcript.is_type(event.type):
            transcript = Transcript.from_event(event)
            lang = transcript.language or "en"
            text = transcript.text or ""

            device_id: Optional[str] = None
            satellite_id: Optional[str] = None
            if transcript.context:
                device_id = transcript.context.get("device_id")
                satellite_id = transcript.context.get("satellite_id")

            # DEBUG
            device_id = "0419d58f1f161dfe9e327a2ed9c9f47e"
            satellite_id = (
                "assist_satellite.home_assistant_voice_090087_assist_satellite"
            )

            _LOGGER.debug(
                "Processing transcript with language '%s': %s (device_id=%s, satellite_id=%s)",
                lang,
                text,
                device_id,
                satellite_id,
            )

            if not text.strip():
                _LOGGER.debug("No command")
                await self.write_event(
                    NotHandled(
                        text=_ERROR_NO_COMMAND, context=transcript.context
                    ).event()
                )
                return True

            lang_intents = self.loader.get_intents(lang)
            if lang_intents is None:
                _LOGGER.debug("No intents for language: %s", lang)
                await self.write_event(
                    NotHandled(
                        text=_ERROR_LANGUAGE_NOT_SUPPORTED.format(language=lang),
                        context=transcript.context,
                    ).event()
                )
                return True

            is_handled, response_text = await async_converse(
                self.hass,
                text,
                lang_intents,
                device_id=device_id,
                satellite_id=satellite_id,
            )

            if is_handled:
                await self.write_event(
                    Handled(text=response_text, context=transcript.context).event()
                )
            else:
                await self.write_event(
                    NotHandled(text=response_text, context=transcript.context).event()
                )

            return True

        if Describe.is_type(event.type):
            await self.write_event(
                Info(
                    handle=[
                        HandleProgram(
                            name="default-agent",
                            description="Default Agent",
                            attribution=Attribution(
                                name="OHF Voice", url="https://github.com/OHF-Voice"
                            ),
                            installed=True,
                            version="0.0.1",
                            models=[
                                HandleModel(
                                    name="default-agent",
                                    description="Default Agent",
                                    attribution=Attribution(
                                        name="OHF Voice",
                                        url="https://github.com/OHF-Voice",
                                    ),
                                    installed=True,
                                    version=version("home_assistant_intents"),
                                    languages=get_languages(),
                                )
                            ],
                        )
                    ]
                ).event()
            )
            return True

        return True


if __name__ == "__main__":
    asyncio.run(main())
