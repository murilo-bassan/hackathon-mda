from general_process.core.state.state import State
from process_incident.core.subgraph_incident_builder import build_incident_subgraph

from functools import lru_cache

@lru_cache(maxsize=1)
def get_compiled_graph():
    """Lazy singleton thread-safe via lru_cache."""
    return build_incident_subgraph()

incident_subgraph = build_incident_subgraph()

def incident_workflow(state: State) -> dict:
    incident_subgraph = get_compiled_graph()

    raw_input = dict(state.get("raw_input") or {})

    result = incident_subgraph.invoke({"incident": raw_input})

    return {
        "result": result
    }
