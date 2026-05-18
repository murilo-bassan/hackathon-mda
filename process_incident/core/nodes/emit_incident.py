import csv
import json
import os
from process_incident.core.state.incident_state import State
from process_incident.utilities.config import RESPONSES_PATH, REPORT_CSV
from general_process.utilities.logger_config import setup_logger

# Inicializando o logger padronizado
logger = setup_logger(__name__)

def emit_incident(state: State) -> dict:
    incident = state.get("incident", {})

    os.makedirs(RESPONSES_PATH, exist_ok=True)

    response = {
        "id": incident["id"],
        "category": incident.get("category", ""),
        "category_justification": incident.get("category_justification", ""),
        "critical": incident.get("critical", False),
        "critical_justification": incident.get("critical_justification", ""),
        "scope": incident.get("scope", ""),
        "affected_systems": incident.get
        ("affected_systems", ""),
        "responsible_person": incident.get("responsible_person", ""),
        "contact_info": incident.get("contact_info", ""),
        "containment_steps": incident.get("containment_steps", []),
        "containment_justification": incident.get("containment_justification", ""),
        "alert_draft": incident.get("alert_draft", ""),
        "report_template": incident.get("report_template", ""),
    }

    # Substituindo os prints poluídos pelo logger
    ticket_id = incident.get("id", "UNKNOWN")
    logger.info(f"Emitindo resultados para o Ticket {ticket_id}")

    # SALVAR JSON INDIVIDUAL
    with open(RESPONSES_PATH / f"incident_{incident.get("id")}.json", "w", encoding="utf-8") as f:
        json.dump(response, f, ensure_ascii=False, indent=2)

    # GERAR / ATUALIZAR CSV
    file_exists = REPORT_CSV.is_file()

    with open(REPORT_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=response.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(response)

    return {
        "incident": response
    }
