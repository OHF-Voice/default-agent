import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from hassil import Intents, merge_dict
from home_assistant_intents import get_intents, get_languages

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
        self, custom_sentences_dirs: Optional[Iterable[Union[str, Path]]] = None
    ) -> None:
        self.lang_intents: Dict[str, LanguageIntents] = {}
        self.lang_map: Dict[str, str] = {lang: lang for lang in get_languages()}

        if custom_sentences_dirs is not None:
            self.custom_sentences_dirs = [Path(p) for p in custom_sentences_dirs]
        else:
            self.custom_sentences_dirs = []

        # Get supported languages from custom sentences
        for sentences_dir in self.custom_sentences_dirs:
            for lang_dir in sentences_dir.iterdir():
                if not lang_dir.is_dir():
                    continue

                lang = lang_dir.name
                self.lang_map.setdefault(lang, lang)

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
        intents_dict = get_intents(language)
        if (not intents_dict) and (language not in self.lang_map):
            # Language isn't supported
            _LOGGER.debug("Language isn't supported: %s", original_language or language)
            return None

        _LOGGER.debug(
            "Loading intents for %s (requested=%s)", language, original_language
        )

        intents_dict = intents_dict or {}
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
