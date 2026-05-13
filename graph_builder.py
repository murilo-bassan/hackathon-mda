from langgraph.graph import END, START, StateGraph
from state.state import State
from nodes.ingest import ingest
from nodes.classify_type import classify_type
from nodes.score_priority import score_priority
from utilities.decide_response import decide_response
from utilities.validation_response import validation_response
from nodes.draft_response import draft_response
from nodes.emit import emit
from nodes.queue_only import queue_only

def build_graph():

    builder = StateGraph(State)

    # Registro dos nós
    builder.add_node("ingest", ingest)
    builder.add_node("classify_type", classify_type)
    builder.add_node("score_priority", score_priority)
    builder.add_node("draft_response", draft_response)
    builder.add_node("queue_only", queue_only)
    builder.add_node("emit", emit)

    # Arestas normais (fluxo sequencial principal)
    builder.add_edge(START, "ingest")

    # Aresta condicional: após validation, decide o próximo nó
    builder.add_conditional_edges(
        "ingest",
        validation_response,
        {
            "classify_type": "classify_type",
            "emit": "emit",
        }
    )

    builder.add_edge("classify_type", "score_priority")

    # Aresta condicional: após route, decide o próximo nó
    builder.add_conditional_edges(
        "score_priority",
        decide_response,
        {
            "draft_response": "draft_response",
            "queue_only": "queue_only",
        }
    )

    # draft_response sempre desemboca em emit
    builder.add_edge("draft_response", "emit")
    builder.add_edge("queue_only", "emit")
    builder.add_edge("emit", END)

    return builder.compile()


graph = build_graph()