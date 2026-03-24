from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any
from jinja2 import Environment
import re


_TEMPLATE_PATTERN = re.compile(r"{{|{%|{#")


@dataclass
class Target:
    entity_id: Optional[Union[str, List[str]]] = None
    area_id: Optional[Union[str, List[str]]] = None
    floor_id: Optional[Union[str, List[str]]] = None


@dataclass
class Intent:
    name: str
    data: Optional[Dict[str, Any]] = None


@dataclass
class Action:
    action: str
    target: Optional[Target] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class Condition:
    condition: str


@dataclass
class Sequence:
    actions: List[Union[Action, Intent]]


@dataclass
class ChooseAction:
    conditions: List[Condition]
    sequence: Sequence
    default: Optional[Sequence] = None


@dataclass
class IntentActions:
    match_targets: bool
    actions: List[Any]
    slot_templates: Dict[str, str]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "IntentActions":
        return IntentActions(
            match_targets=data["match_targets"],
            actions=parse_actions(data["actions"]),
            slot_templates=data["slots"],
        )

    def evaluate_actions(self, env: Environment, variables: Dict[str, Any]) -> List[Union[Action, Intent]]:
        result: List[Union[Action, Intent]] = []
        for action in self.actions:
            if isinstance(action, Action):
                result.append(self._evaluate_action(action, env, variables))
            elif isinstance(action, Intent):
                result.append(self._evaluate_intent(action, env, variables))
            elif isinstance(action, Sequence):
                for seq_action in action.actions:
                    if isinstance(seq_action, Action):
                        result.append(self._evaluate_action(seq_action, env, variables))
                    elif isinstance(seq_action, Intent):
                        result.append(self._evaluate_intent(seq_action, env, variables))
                    else:
                        result.append(seq_action)
            elif isinstance(action, ChooseAction):
                for condition in action.conditions:
                    template = env.from_string(condition.condition)
                    if template.render(**variables):
                        for seq_action in action.sequence.actions:
                            if isinstance(seq_action, Action):
                                result.append(self._evaluate_action(seq_action, env, variables))
                            elif isinstance(seq_action, Intent):
                                result.append(self._evaluate_intent(seq_action, env, variables))
                            else:
                                result.append(seq_action)
                        break
                else:
                    if action.default:
                        for seq_action in action.default.actions:
                            if isinstance(seq_action, Action):
                                result.append(self._evaluate_action(seq_action, env, variables))
                            elif isinstance(seq_action, Intent):
                                result.append(self._evaluate_intent(seq_action, env, variables))
                            else:
                                result.append(seq_action)
        return result

    def _evaluate_intent(self, intent: Intent, env: Environment, variables: Dict[str, Any]) -> Intent:
        name = self._render_if_template(intent.name, env, variables)
        data = None
        if intent.data:
            data = {}
            for key, value in intent.data.items():
                data[key] = self._render_if_template(value, env, variables)
        return Intent(name=name, data=data)

    def _evaluate_action(self, action: Action, env: Environment, variables: Dict[str, Any]) -> Union[Action, Intent]:
        action_str = self._render_if_template(action.action, env, variables)
        
        target = None
        if action.target:
            entity_id = self._render_if_template(action.target.entity_id, env, variables)
            area_id = self._render_if_template(action.target.area_id, env, variables)
            floor_id = self._render_if_template(action.target.floor_id, env, variables)
            target = Target(entity_id=entity_id, area_id=area_id, floor_id=floor_id)
        
        data = None
        if action.data:
            data = {}
            for key, value in action.data.items():
                data[key] = self._render_if_template(value, env, variables)
        
        return Action(action=action_str, target=target, data=data)

    def _render_if_template(self, value: Any, env: Environment, variables: Dict[str, Any]) -> Any:
        if isinstance(value, str):
            if _TEMPLATE_PATTERN.search(value):
                template = env.from_string(value)
                return template.render(**variables)
        elif isinstance(value, list):
            return [self._render_if_template(item, env, variables) for item in value]
        return value


def action_from_dict(data: Dict[str, Any]) -> Union[Action, Intent]:
    if "intent" in data:
        return Intent(
            name=data["intent"],
            data=data.get("data"),
        )
    
    target = None
    if "target" in data and data["target"]:
        target_data = data["target"]
        target = Target(
            entity_id=target_data.get("entity_id"),
            area_id=target_data.get("area_id"),
            floor_id=target_data.get("floor_id"),
        )
    return Action(
        action=data.get("action", ""),
        target=target,
        data=data.get("data"),
    )


def sequence_from_dict(data: Dict[str, Any]) -> Sequence:
    actions = []
    if "sequence" in data:
        for seq_item in data["sequence"]:
            if isinstance(seq_item, dict):
                actions.append(action_from_dict(seq_item))
    return Sequence(actions=actions)


def condition_from_dict(data: Dict[str, Any]) -> Condition:
    return Condition(condition=data.get("condition", ""))


def choose_from_dict(data: Dict[str, Any]) -> ChooseAction:
    conditions = []
    sequence = None
    default = None

    if "choose" in data:
        for item in data["choose"]:
            if "conditions" in item:
                for cond in item["conditions"]:
                    conditions.append(condition_from_dict(cond))
            if "sequence" in item:
                sequence = sequence_from_dict(item)

    if "default" in data and data["default"]:
        default = sequence_from_dict({"sequence": data["default"]})

    return ChooseAction(
        conditions=conditions,
        sequence=sequence if sequence else Sequence(actions=[]),
        default=default,
    )


def parse_actions(actions: List[Any]) -> List[Any]:
    parsed = []
    for action in actions:
        if isinstance(action, dict):
            if "choose" in action:
                parsed.append(choose_from_dict(action))
            else:
                parsed.append(action_from_dict(action))
        else:
            parsed.append(action)
    return parsed
