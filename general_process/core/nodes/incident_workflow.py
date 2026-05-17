from general_process.core.state.state import State
from process_incident.core.subgraph_incident_builder import build_incident_subgraph

incident_subgraph = build_incident_subgraph()

def incident_workflow(state: State) -> dict:
    
    raw_input = dict(state.get("raw_input") or {})

    result = incident_subgraph.invoke({"incident": raw_input})

    return {
        "result": result
    }
