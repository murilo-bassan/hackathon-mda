import json
from datetime import datetime
from state import State
from typing import List

def emit(state: State) -> dict:
    ticket = state["ticket"]
    partial = state.get("response", {})

    response = {
        "ticket_id": ticket["id"],
        "category": partial.get("category"),
        "urgency": partial.get("urgency", 0),
        "impact": partial.get("impact", 0),
        "resulting_priority": partial.get("resulting_priority", 0),
        "priority_justification": partial.get("priority_justification", ""),
        "service_type": partial.get("service_type", ""),
        "support_level": partial.get("support_level", 1),
        "category_justification": partial.get("category_justification", ""),
        "department": partial.get("department", ""),
        "response_draft": partial.get("response_draft", ""),
    }

    print("\n" + "=" * 60)
    print(f"LOG — Ticket {ticket['id']}")
    print("=" * 60)
    print(json.dumps(response, ensure_ascii=False, indent=2))

    
    closing = (
        "Seu chamado foi encerrado pela equipe da AGETIC/UFMS. "
        "Caso o problema persista, reabra o chamado ou entre em contato: "
        "suporte.agetic@ufms.br | (67) 3345-7292."
    )

    return {
        "response": response,
        "closing_message": closing,
    }