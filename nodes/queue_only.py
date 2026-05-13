import json
from datetime import datetime
from state.state import State
from utilities.config import QUEUE_PATH
from utilities.logger_config import setup_logger

logger = setup_logger(__name__)

def queue_only(state: State) -> dict:
    ticket = state["ticket"]
    partial = state.get("response", {})

    entry = {
        "timestamp": datetime.now().isoformat(),
        "ticket_id": ticket["id"],
        "free_text": ticket["free_text"],
        "category": partial.get("category"),
        "priority": partial.get("resulting_priority"),
        "department": partial.get("department"),
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

    # Trocando print pelo logger
    logger.info(f"Ticket {ticket['id']} adicionado à fila humana. Total: {len(queue)}")

    partial_out = dict(partial)
    partial_out["response_draft"] = "[FILA HUMANA] Encaminhado ao analista responsável."
    return {"response": partial_out}