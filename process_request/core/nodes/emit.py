import csv
import json
import os
from process_request.core.state.request_state import State
from process_request.utilities.config import RESPONSES_PATH, REPORT_CSV
from general_process.utilities.logger_config import setup_logger

# Inicializando o logger padronizado
logger = setup_logger(__name__)

def emit(state: State) -> dict:
    ticket = state.get("ticket", {})
    partial = state.get("response", {})

    os.makedirs(RESPONSES_PATH, exist_ok=True)

    closing = (
        "Seu chamado foi encerrado pela equipe da AGETIC/UFMS. "
        "Caso o problema persista, reabra o chamado ou entre em contato: "
        "suporte.agetic@ufms.br | (67) 3345-7292."
    )

    response = {
        "ticket_id": ticket.get("id", ""),
        "category": partial.get("category", ""),
        "urgency": partial.get("urgency", 0),
        "impact": partial.get("impact", 0),
        "resulting_priority": partial.get("resulting_priority", 0),
        "priority_justification": partial.get("priority_justification", ""),
        "service_type": partial.get("service_type", ""),
        "support_level": partial.get("support_level", 1),
        "category_justification": partial.get("category_justification", ""),
        "department": partial.get("department", ""),
        "response_draft": partial.get("response_draft", ""),
        "closing_message": closing,
        "needs_more_info": ticket.get("needs_more_info", False),
        "info_justification": ticket.get("info_justification", ""),
        "validation_status": partial.get("validation_status", "pending")
    }

    # Substituindo os prints poluídos pelo logger
    ticket_id = ticket.get("id", "UNKNOWN")
    logger.info(f"Emitindo resultados para o Ticket {ticket_id}")

    # SALVAR JSON INDIVIDUAL
    with open(RESPONSES_PATH / f"ticket_{ticket.get("id")}.json", "w", encoding="utf-8") as f:
        json.dump(response, f, ensure_ascii=False, indent=2)

    # GERAR / ATUALIZAR CSV
    file_exists = REPORT_CSV.is_file()

    with open(REPORT_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=response.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(response)

    return {
        "response": response,
    }
