"""Wyoming conversation agent."""

import argparse
import asyncio
import logging
from functools import partial
from importlib.metadata import version
from typing import Optional

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
        "--custom-sentences",
        action="append",
        help="Directory with <language>/<sentences.yaml> files",
    )
    parser.add_argument(
        "--intents-repo",
        help="Path to intents repository directory (implies --no-builtin-intents)",
    )
    parser.add_argument(
        "--no-builtin-intents",
        action="store_true",
        help="Don't load intents from home-assistant-intents package",
    )
    parser.add_argument(
        "--disable-intent",
        action="append",
        help="Disable a specific intent by name",
    )
    #
    parser.add_argument(
        "--device-id",
        help="Default satellite device id when not provided by Home Assistant (for debugging)",
    )
    parser.add_argument(
        "--satellite-id",
        help="Default satellite entity id when not provided by Home Assistant (for debugging)",
    )
    #
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to log"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    _LOGGER.debug(args)

    hass = HomeAssistant(token=args.hass_token, api_url=args.hass_api)
    loader = IntentsLoader(
        custom_sentences_dirs=args.custom_sentences,
        intents_repo_dir=args.intents_repo,
        load_builtin_intents=(not args.no_builtin_intents),
        disabled_intents=args.disable_intent,
    )

    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Ready")
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

            # The device/satellite ids are used to determine which area to
            # target for commands like "turn on the lights" that don't name an
            # area explicitly.
            #
            # In YAML, these commands look like:
            # - sentences:
            #     - "turn on [the] lights"
            #   slots:
            #     domain: "light"
            #   requires_context:  <--- required
            #     area:
            #       slot: true
            device_id: Optional[str] = None
            satellite_id: Optional[str] = None
            if transcript.context:
                device_id = transcript.context.get("device_id")
                satellite_id = transcript.context.get("satellite_id")

            device_id = device_id or self.args.device_id
            satellite_id = satellite_id or self.args.satellite_id

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

            # Try to load intents for the requested language.
            #
            # We try the full language code first, like "en_US". If there are no
            # intents, then the language family is tried instead ("en" in this
            # example).
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

            # 1. Recognize the intent
            # 2. If recognized, handle in Home Assistant via /api/intent/handle
            # 3. Use the result from Home Assistant and response template to
            #    generate a text response
            is_handled, response_text = await async_converse(
                self.hass,
                text,
                lang_intents,
                self.loader.get_intent_handlers(),
                device_id=device_id,
                satellite_id=satellite_id,
            )

            if is_handled:
                # Success, return resopnse
                await self.write_event(
                    Handled(text=response_text, context=transcript.context).event()
                )
            else:
                # Failure, return error
                await self.write_event(
                    NotHandled(text=response_text, context=transcript.context).event()
                )

            return True

        if Describe.is_type(event.type):
            # Send information about the conversation agent to Home Assistant.
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
                            version=version("default_agent"),
                            models=[
                                HandleModel(
                                    name="default-agent",
                                    description="Default Agent",
                                    attribution=Attribution(
                                        name="OHF Voice",
                                        url="https://github.com/OHF-Voice",
                                    ),
                                    installed=True,
                                    version=(
                                        version("home_assistant_intents")
                                        if self.loader.load_builtin_intents
                                        else "dev"
                                    ),
                                    languages=self.loader.supported_languages(),
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
