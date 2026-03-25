from ..intent_handler import IntentHandler, HandleInput, HandleOutput


class GetStateHandler(IntentHandler):
    intent_type = "HassGetState"
    match_targets = True

    async def handle(self, input: HandleInput) -> HandleOutput:
        state_value = input.intent_result.entities.get("state")
        if state_value is None:
            state_names = None
        else:
            value = state_value.value
            if isinstance(value, list):
                state_names = set(value)
            else:
                state_names = {value}

        matched_states: list = []
        unmatched_states: list = []

        for state in input.target_states:
            if (not state_names) or (state.state in state_names):
                matched_states.append(state)
            else:
                unmatched_states.append(state)

        return HandleOutput(
            success=True,
            matched_states=matched_states,
            unmatched_states=unmatched_states,
        )