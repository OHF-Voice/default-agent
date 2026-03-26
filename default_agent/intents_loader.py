"""Loader for HassIL intents."""

import importlib
import inspect
import logging
import pkgutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator, List, Optional, Type, Union

import yaml
from hassil import Intents, merge_dict
from home_assistant_intents import get_intents, get_languages

import default_agent.intents

from .intent_handler import IntentHandler

_LOGGER = logging.getLogger(__name__)


@dataclass
class LanguageIntents:
    """Loaded intents for a language."""

    language: str
    intents: Intents
    intents_dict: Dict[str, Any]
    intent_responses: Dict[str, Any]
    error_responses: Dict[str, Any]


class IntentsLoader:
    def __init__(
        self,
        custom_sentences_dirs: Optional[Iterable[Union[str, Path]]] = None,
        intents_repo_dir: Optional[Union[str, Path]] = None,
        load_builtin_intents: bool = True,
        disabled_intents: Optional[List[str]] = None,
    ) -> None:
        self.lang_intents: Dict[str, LanguageIntents] = {}
        self.lang_map: Dict[str, str] = {}
        self.load_builtin_intents = load_builtin_intents
        self.disabled_intents = disabled_intents or []
        self._intent_handlers: Optional[Dict[str, IntentHandler]] = None

        self.intents_repo_dir: Optional[Path] = None
        if intents_repo_dir:
            self.intents_repo_dir = Path(intents_repo_dir)
            self.load_builtin_intents = False

        if custom_sentences_dirs is not None:
            self.custom_sentences_dirs = [Path(p) for p in custom_sentences_dirs]
        else:
            self.custom_sentences_dirs = []

        self._find_supported_languages()

    def get_intents(self, language: str) -> Optional[LanguageIntents]:
        lang_intents = self.lang_intents.get(language)
        if lang_intents is not None:
            # Cached
            _LOGGER.debug("Using cached intents for %s", language)
            return lang_intents

        original_language = language
        mapped_lang = self.lang_map.get(language)
        if mapped_lang is not None:
            return self._load_intents(mapped_lang, original_language)

        # en-US -> en-us
        language = language.lower().replace("_", "-")
        mapped_lang = self.lang_map.get(language)

        if mapped_lang is not None:
            return self._load_intents(mapped_lang, original_language)

        if "-" not in language:
            # Language isn't supported
            return None

        # en-us -> en
        language = language.split("-", maxsplit=1)[0]
        mapped_lang = self.lang_map.get(language)

        if mapped_lang is not None:
            return self._load_intents(mapped_lang, original_language)

        # Language isn't supported
        _LOGGER.debug("Language isn't supported: %s", original_language)
        return None

    def _load_intents(
        self, language: str, original_language: Optional[str] = None
    ) -> Optional[LanguageIntents]:
        intents_dict: Dict[str, Any] = {}

        if self.load_builtin_intents:
            # Built-in intents
            builtin_intents_dict = get_intents(language)
            if builtin_intents_dict:
                merge_dict(intents_dict, builtin_intents_dict)
                _LOGGER.debug(
                    "Loaded built-in intents for %s (requested=%s)",
                    language,
                    original_language,
                )
        elif self.intents_repo_dir:
            # Intents repo
            sentences_dir = self.intents_repo_dir / "sentences"
            responses_dir = self.intents_repo_dir / "responses"
            for yaml_dir in (sentences_dir, responses_dir):
                for lang_dir in yaml_dir.iterdir():
                    if not lang_dir.is_dir():
                        continue

                    yaml_lang = lang_dir.name
                    if yaml_lang != language:
                        continue

                    for yaml_path in lang_dir.glob("*.yaml"):
                        _LOGGER.debug("Loading repo file: %s", yaml_path)
                        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
                            merge_dict(intents_dict, yaml.safe_load(yaml_file))

        # Custom sentences
        for sentences_dir in self.custom_sentences_dirs:
            for sentences_lang_dir in sentences_dir.iterdir():
                if not sentences_lang_dir.is_dir():
                    continue

                sentences_lang = sentences_lang_dir.name
                if sentences_lang != language:
                    continue

                for sentences_path in sentences_lang_dir.glob("*.yaml"):
                    _LOGGER.debug("Loading custom sentences file: %s", sentences_path)
                    with open(sentences_path, "r", encoding="utf-8") as sentences_file:
                        merge_dict(intents_dict, yaml.safe_load(sentences_file))

        if not intents_dict:
            # Language isn't supported
            _LOGGER.debug(
                "Language isn't supported or no sentences available: %s",
                original_language or language,
            )
            return None

        if self.disabled_intents:
            intents_to_remove = [
                key
                for key in intents_dict.get("intents", {})
                if key in self.disabled_intents
            ]
            for key in intents_to_remove:
                del intents_dict["intents"][key]

            _LOGGER.debug("Disabled intents: %s", intents_to_remove)

        responses_dict = intents_dict.get("responses", {})

        lang_intents = LanguageIntents(
            language=(original_language or language),
            intents=Intents.from_dict(intents_dict),
            intents_dict=intents_dict,
            intent_responses=responses_dict.get("intents", {}),
            error_responses=responses_dict.get("errors", {}),
        )

        self.lang_intents[language] = lang_intents

        if original_language:
            # Faster loading next time
            self.lang_map[original_language] = language
            self.lang_intents[original_language] = lang_intents

        return lang_intents

    def supported_languages(self) -> List[str]:
        return sorted(self.lang_map.keys())

    def _find_supported_languages(self) -> None:
        """Search intents package and directories for supported languages."""
        if self.intents_repo_dir:
            # Get supported languages from intents repo
            sentences_dir = self.intents_repo_dir / "sentences"
            _LOGGER.debug("Scanning directory for languages: %s", sentences_dir)
            for lang_dir in sentences_dir.iterdir():
                if not lang_dir.is_dir():
                    continue

                if any(lang_dir.glob("*.yaml")):
                    lang = lang_dir.name
                    self.lang_map.setdefault(lang, lang)

        if self.load_builtin_intents:
            # Get supported languages from built-in intents
            self.lang_map.update({lang: lang for lang in get_languages()})

        # Get supported languages from custom sentences
        for sentences_dir in self.custom_sentences_dirs:
            _LOGGER.debug("Scanning directory for languages: %s", sentences_dir)
            for lang_dir in sentences_dir.iterdir():
                if not lang_dir.is_dir():
                    continue

                if any(lang_dir.glob("*.yaml")):
                    lang = lang_dir.name
                    self.lang_map.setdefault(lang, lang)

        _LOGGER.debug("Supported languages: %s", sorted(self.lang_map.keys()))

    def get_intent_handlers(
        self,
    ) -> Dict[str, IntentHandler]:
        """Find all intent handler subclasses in default_agent.intents (loaded once)."""
        if self._intent_handlers is not None:
            return self._intent_handlers

        handlers_dict: Dict[str, IntentHandler] = {}
        for handle_type in find_intent_handlers(default_agent.intents):
            _LOGGER.debug(
                "Loaded intent handler: %s for %s",
                handle_type,
                handle_type.intent_type,
            )
            handlers_dict[handle_type.intent_type] = handle_type()

        self._intent_handlers = handlers_dict
        return self._intent_handlers


def find_intent_handlers(
    package: ModuleType,
) -> List[Type[IntentHandler]]:
    """
    Find all subclasses of `base_class` inside `package`.
    """

    subclasses: List[Type[IntentHandler]] = []
    for module in _iter_submodules(package):
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Ensure:
            # - subclass of base_class
            # - not the base class itself
            # - defined in this module (not imported)
            if (
                issubclass(obj, IntentHandler)
                and obj is not IntentHandler
                and obj.__module__ == module.__name__
            ):
                subclasses.append(obj)

    return subclasses


def _iter_submodules(module: ModuleType) -> Iterator[ModuleType]:
    """
    Yield the given module, plus any submodules if it is a package.
    """
    yield module

    module_path = getattr(module, "__path__", None)
    if module_path is None:
        return

    prefix = module.__name__ + "."
    for module_info in pkgutil.walk_packages(module_path, prefix):
        try:
            yield importlib.import_module(module_info.name)
        except Exception as err:
            _LOGGER.error("Failed to import %s: %s", module_info.name, err)
