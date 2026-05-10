import json
from datetime import datetime
from state import State

QUEUE_PATH = "data/human_queue.json"

def queue_only(state: State) -> dict:
    idx = state.get("current_ticket_index", 0)
    ticket = state["tickets"][idx]

    entry = {
        "timestamp": datetime.now().isoformat(),
        "ticket_id": ticket["id"],
        "free_text": ticket["free_text"],
        "category": state.get("_current_category"),
        "priority": state.get("_current_priority"),
        "department": state.get("_current_department"),
        "reason": "Alta prioridade ou categoria complexa — requer analista humano.",
    }

    try:
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            queue = json.load(f)
    except FileNotFoundError:
        queue = []

    queue.append(entry)

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    print(f"[queue_only] Ticket {ticket['id']} adicionado à fila. Total: {len(queue)}")
    return {"_current_draft": "[FILA HUMANA] Encaminhado ao analista responsável."}