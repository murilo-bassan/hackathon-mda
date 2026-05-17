from langgraph.graph import END, START, StateGraph

from general_process.core.nodes.prepare_incident import prepare_incident
from general_process.core.nodes.classify_input import classify_input
from general_process.core.nodes.normalize_input import normalize_input
from general_process.core.nodes.request_workflow import request_workflow
from general_process.core.nodes.incident_workflow import incident_workflow

from general_process.core.state.state import State
from general_process.utilities.decide_input import decide_input


def build_graph():

    builder = StateGraph(State)

    # Registro de nós gerais
    builder.add_node("normalize_input", normalize_input)
    builder.add_node("classify_input", classify_input)

    # Subgraphs
    builder.add_node("request_workflow", request_workflow)
    builder.add_node("incident_workflow", incident_workflow)

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
