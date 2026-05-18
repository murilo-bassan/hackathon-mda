from general_process.core.state.state import State
from process_request.core.subgraph_request_builder import build_request_subgraph

from functools import lru_cache

@lru_cache(maxsize=1)
def get_compiled_graph():
    """Lazy singleton thread-safe via lru_cache."""
    return build_request_subgraph()


def request_workflow(state: State) -> dict:
    request_subgraph = get_compiled_graph()

    raw_input = dict(state.get("raw_input") or {})

    result = request_subgraph.invoke({"ticket": raw_input})

    return {
        "result": result
    }
