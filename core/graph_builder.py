from langgraph.graph import END, START, StateGraph

from core.nodes_general.classify_input import classify_input
from core.nodes_general.normalize_input import normalize_input
from core.state.state import State

from utilities.decide_input import decide_input

from subgraph_request_builder import build_request_subgraph
from subgraph_incident_builder import build_incident_subgraph

def build_graph():

    request_subgraph = build_request_subgraph()
    incident_subgraph = build_incident_subgraph()

    builder = StateGraph(State)

    # Registro de nós gerais
    builder.add_node("normalize_input", normalize_input)
    builder.add_node("classify_input", classify_input)

    # Subgraphs
    builder.add_node("request_workflow", request_subgraph)
    builder.add_node("incident_workflow", incident_subgraph)

    # Arestas normais (fluxo sequencial principal)
    builder.add_edge(START, "normalize_input")
    builder.add_edge("normalize_input", "classify_input")

    builder.add_conditional_edges(
        "classify_input",
        decide_input,
        {
            "request": "request_workflow",
            "incident": "incident_workflow",
        }
    )

    builder.add_edge("request_workflow", END)
    builder.add_edge("incident_workflow", END)

    return builder.compile()


graph = build_graph()