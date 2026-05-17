from general_process.core.state.state import State
from process_request.core.subgraph_request_builder import build_request_subgraph

request_subgraph = build_request_subgraph()

def request_workflow(state: State) -> dict:
    
    raw_input = dict(state.get("raw_input") or {})

    result = request_subgraph.invoke({"ticket": raw_input})

    return {
        "result": result
    }
