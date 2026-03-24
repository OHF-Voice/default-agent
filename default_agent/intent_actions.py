from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class Target:
    entity_id: Optional[str | List[str]] = None
    area_id: Optional[str | List[str]] = None
    floor_id: Optional[str | List[str]] = None


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
    actions: List[Action]


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


def action_from_dict(data: Dict[str, Any]) -> Action:
    target = None
    if "target" in data and data["target"]:
        target_data = data["target"]
        target = Target(
            entity_id=target_data.get("entity_id"),
            area_id=target_data.get("area_id"),
            floor_id=target_data.get("floor_id"),
        )
    return Action(
        action=data["action"],
        target=target,
        data=data.get("data"),
    )


def sequence_from_dict(data: Dict[str, Any]) -> Sequence:
    actions = []
    if "sequence" in data:
        for seq_item in data["sequence"]:
            if isinstance(seq_item, dict):
                actions.append(action_from_dict(seq_item))
            else:
                actions.append(seq_item)
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
            elif "condition" in action or "sequence" in action:
                parsed.append(sequence_from_dict(action))
            else:
                parsed.append(action_from_dict(action))
        else:
            parsed.append(action)
    return parsed