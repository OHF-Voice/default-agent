import importlib
import inspect
import logging
import pkgutil
from abc import abstractmethod
from collections.abc import Collection
from dataclasses import dataclass
from types import ModuleType
from typing import Any, ClassVar, Dict, Iterator, List, Optional, Type, Union

from hassil import RecognizeResult
from jinja2 import Environment

from .hass_api import HomeAssistant, InfoForRecognition, State
from .models import LanguageIntents
from .name_matcher import (
    MatchTargetsConstraints,
    MatchTargetsPreferences,
    MatchTargetsResult,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class HandleInput:
    text: str
    lang_intents: LanguageIntents
    hass: HomeAssistant
    hass_info: InfoForRecognition
    intent_result: RecognizeResult
    target_states: List[State]
    target_entity_ids: List[str]
    template_env: Environment
    template_vars: Dict[str, Any]

    device_id: Optional[str] = None
    satellite_id: Optional[str] = None

    match_result: Optional[MatchTargetsResult] = None
    match_domain: Optional[str] = None
    match_constraints: Optional[MatchTargetsConstraints] = None
    match_preferences: Optional[MatchTargetsPreferences] = None

    @property
    def language(self) -> str:
        return self.lang_intents.language


@dataclass
class HandleOutput:
    success: bool
    response_vars: Optional[Dict[str, Any]] = None
    response_text: Optional[str] = None
    matched_states: Optional[List[State]] = None
    unmatched_states: Optional[List[State]] = None


class IntentHandler:
    intent_type: ClassVar[str]
    match_targets: ClassVar[bool]
    required_states: Optional[Union[str, Collection[str]]] = None
    required_features: Optional[int] = None
    inferred_domain: Optional[Union[str, Collection[str]]] = None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        for attr_name in ("intent_type", "match_targets"):
            if not hasattr(cls, attr_name):
                raise TypeError(f"{cls.__name__} must define {attr_name}")

    @abstractmethod
    async def handle(self, handle_input: HandleInput) -> HandleOutput:
        pass


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
