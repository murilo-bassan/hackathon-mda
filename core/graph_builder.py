from langgraph.graph import END, START, StateGraph
from core.nodes_35.classify_criticality import classify_criticality
from core.nodes_35.draft_alert import draft_alert
from core.nodes_35.emit_incident import emit_incident
from core.nodes_35.ingest_incident import ingest_incident
from core.nodes_35.lookup_owner import lookup_owner
from core.nodes_35.recommend_containment import recommend_containment
from core.nodes_35.request_report import request_report
from core.nodes_general.classify_input import classify_input
from core.nodes_general.normalize_input import normalize_input
from core.state.state import State
from core.nodes.ingest import ingest
from utilities.decide_input import decide_input
from utilities.decide_content import decide_content
from utilities.validation_response import validation_response
from core.nodes.validate_input import validate_input
from core.nodes.draft_request import draft_request
from core.nodes.classify_type import classify_type
from core.nodes.score_priority import score_priority
from utilities.decide_response import decide_response_from_state
from core.nodes.draft_response import draft_response
from core.nodes.emit import emit
from core.nodes.queue_only import queue_only

def build_graph():

    builder = StateGraph(State)

    #Registro de nós gerais
    builder.add_node("normalize_input", normalize_input)
    builder.add_node("classify_input", classify_input)

    # Registro dos nós - 3.1
    builder.add_node("ingest", ingest)
    builder.add_node("validate_input", validate_input)
    builder.add_node("draft_request", draft_request)
    builder.add_node("classify_type", classify_type)
    builder.add_node("score_priority", score_priority)
    builder.add_node("draft_response", draft_response)
    builder.add_node("queue_only", queue_only)
    builder.add_node("emit", emit)

    # Registro dos nós - 3.5
    builder.add_node("ingest_incident", ingest_incident)
    builder.add_node("classify_criticality", classify_criticality)
    builder.add_node("lookup_owner", lookup_owner)
    builder.add_node("recommend_containment", recommend_containment)
    builder.add_node("draft_alert", draft_alert)
    builder.add_node("request_report", request_report)
    builder.add_node("emit_incident", emit_incident)

    # Arestas normais (fluxo sequencial principal)
    builder.add_edge(START, "normalize_input")

    builder.add_edge("normalize_input", "classify_input")

    builder.add_conditional_edges(
        "classify_input",
        decide_input,
        {
            "ingest": "ingest",
            "ingest_incident": "ingest_incident",
        }
    )

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


    #fluxo 3.5
    builder.add_edge("ingest_incident", "classify_criticality")
    builder.add_edge("classify_criticality", "lookup_owner")
    builder.add_edge("lookup_owner", "recommend_containment")
    builder.add_edge("recommend_containment", "draft_alert")
    builder.add_edge("draft_alert", "request_report")
    builder.add_edge("request_report", "emit_incident")
    builder.add_edge("emit_incident", END)


    return builder.compile()


graph = build_graph()