from core.state.state import State

def decide_input(state: State) -> dict:
    """
    Decide which input node to execute based on the state of the system.
    """
    """
    if state.get("input_type") == "incident":
        return "ingest_incident"
    else:
        return "ingest"
    """
    return "ingest"