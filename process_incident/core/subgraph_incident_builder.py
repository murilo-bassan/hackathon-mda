from langgraph.graph import END, START, StateGraph

from process_incident.core.state.incident_state import IncidentState

from process_incident.core.nodes.classify_criticality import classify_criticality
from process_incident.core.nodes.draft_alert import draft_alert
from process_incident.core.nodes.emit_incident import emit_incident
from process_incident.core.nodes.ingest_incident import ingest_incident
from process_incident.core.nodes.lookup_owner import lookup_owner
from process_incident.core.nodes.recommend_containment import recommend_containment
from process_incident.core.nodes.request_report import request_report

from process_incident.utilities.incident_validation import incident_validation


def build_incident_subgraph():

    builder = StateGraph(IncidentState)

    # Registro dos nós - 3.5
    builder.add_node("ingest_incident", ingest_incident)
    builder.add_node("classify_criticality", classify_criticality)
    builder.add_node("lookup_owner", lookup_owner)
    builder.add_node("recommend_containment", recommend_containment)
    builder.add_node("draft_alert", draft_alert)
    builder.add_node("request_report", request_report)
    builder.add_node("emit_incident", emit_incident)

    #fluxo 3.5
    builder.add_edge(START, "ingest_incident")

    builder.add_conditional_edges(
        "ingest_incident",
        incident_validation,
        {
            "classify_criticality": "classify_criticality",
            "emit_incident": "emit_incident",
        }
    )

    builder.add_edge("classify_criticality", "lookup_owner")
    builder.add_edge("lookup_owner", "recommend_containment")
    builder.add_edge("recommend_containment", "draft_alert")
    builder.add_edge("draft_alert", "request_report")
    builder.add_edge("request_report", "emit_incident")
    builder.add_edge("emit_incident", END)


    return builder.compile()
