from langgraph.graph import END, START, StateGraph
from state.state import State
from nodes.ingest import ingest
from utilities.decide_content import decide_content
from utilities.validation_response import validation_response
from nodes.validate_input import validate_input
from nodes.draft_request import draft_request
from nodes.classify_type import classify_type
from nodes.score_priority import score_priority
from utilities.decide_response import decide_response_from_state
from nodes.draft_response import draft_response
from nodes.emit import emit
from nodes.queue_only import queue_only

def build_graph():

    builder = StateGraph(State)

    # Registro dos nós
    builder.add_node("ingest", ingest)
    builder.add_node("validate_input", validate_input)
    builder.add_node("draft_request", draft_request)
    builder.add_node("classify_type", classify_type)
    builder.add_node("score_priority", score_priority)
    builder.add_node("draft_response", draft_response)
    builder.add_node("queue_only", queue_only)
    builder.add_node("emit", emit)

    # Arestas normais (fluxo sequencial principal)
    builder.add_edge(START, "ingest")

    # Aresta condicional: após ingest, decide o próximo nó
    builder.add_conditional_edges(
        "ingest",
        validation_response,
        {
            "validate_input": "validate_input",
            "emit": "emit",
        }
    )

    builder.add_edge("classify_type", "score_priority")

    # Aresta condicional: após score_priority, decide o próximo nó
    builder.add_conditional_edges(
        "score_priority",
        decide_response_from_state,
        {
            "draft_response": "draft_response",
            "queue_only": "queue_only",
        }
    )

    # Aresta condicional: após validate_input, decide o próximo nó
    builder.add_conditional_edges(
        "validate_input",
        decide_content,
        {
            "draft_request": "draft_request",
            "classify_type": "classify_type",
        }
    )

    # draft_response sempre desemboca em emit
    builder.add_edge("draft_response", "emit")
    builder.add_edge("queue_only", "emit")
    builder.add_edge("draft_request", "emit")
    builder.add_edge("emit", END)

    return builder.compile()


graph = build_graph()