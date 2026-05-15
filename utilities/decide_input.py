from core.state.state import State

def decide_input(state: State) -> dict:
    """
    Decide which input node to execute based on the state of the system.
    """
    """
    if state.get("input_type") == "incident":
        return {"node": "ingest_incident"}
    else:
        return {"node": "ingest"}
    """
    return {"node": "ingest"}