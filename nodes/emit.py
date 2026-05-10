import json
from datetime import datetime
from state import State
from typing import List

def emit(state: State) -> dict:
    idx = state.get("current_ticket_index", 0)
    ticket = state["tickets"][idx]

    response = {
        "ticket_id": ticket["id"],
        "category": state.get("_current_category", ""),
        "urgency": state.get("urgency", 0),
        "impact": state.get("impact", 0),
        "resulting_priority": state.get("_current_priority", 0),
        "priority_justification": state.get("_current_priority_justification", ""),
        "service_type": state.get("service_type", ""),
        "support_level": state.get("support_level", 1),
        "category_justification": state.get("category_justification", ""),
        "department": state.get("_current_department", ""),
        "response_draft": state.get("_current_draft", ""),
    }

    responses: List = list(state.get("responses", []))
    responses.append(response)

    print("\n" + "=" * 60)
    print(f"LOG — Ticket {ticket['id']}")
    print("=" * 60)
    print(json.dumps(response, ensure_ascii=False, indent=2))

    closing = None
    if state.get("is_finished"):
        closing = (
            "Seu chamado foi encerrado pela equipe da AGETIC/UFMS. "
            "Caso o problema persista, reabra o chamado ou entre em contato: "
            "suporte.agetic@ufms.br | (67) 3345-7292."
        )

    return {
        "responses": responses,
        "closing_message": closing,
    }