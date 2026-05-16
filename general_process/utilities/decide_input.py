from general_process.core.state.state import State

def decide_input(state: State) -> str:
    """
    Decide which workflow to execute based on the classified input type.
    """
    if state.get("input_type") == "incident":
        return "incident"
    return "request"
