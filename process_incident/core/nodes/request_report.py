from process_incident.core.state.incident_state import State
from general_process.utilities.logger_config import setup_logger
from process_incident.utilities.config import REQUEST_REPORT_PROMPT_PATH
from general_process.utilities.prompt_loader import load_prompt
from general_process.utilities.utils import call_llm

logger = setup_logger(__name__)

def request_report(state: State) -> dict:
    """
    Gera o template de Relatório Parcial de Incidente a ser preenchido
    pelo responsável técnico após o acionamento inicial.
    """
    incident = dict(state.get("incident", {}))

    incident_id = incident.get("id", "N/A")
    timestamp = incident.get("timestamp", "N/A")
    category = incident.get("category", "other")
    affected_systems = incident.get("affected_systems", "unknown")
    scope = incident.get("scope", "unknown")
    containment_steps = incident.get("containment_steps", [])
    responsible_person = incident.get("responsible_person", "")

    logger.info(f"Gerando template de relatório para incidente: {incident_id}")

    system_prompt = load_prompt(REQUEST_REPORT_PROMPT_PATH)

    steps_formatted = "\n".join(
        f"[ ] {step}" for step in containment_steps
    ) or "[ ] Nenhuma etapa de contenção definida ainda."

    user_prompt = (
        f"Incident ID: {incident_id}\n"
        f"Timestamp: {timestamp}\n"
        f"Category: {category}\n"
        f"Affected systems: {affected_systems}\n"
        f"Scope: {scope}\n"
        f"Responsible person: {responsible_person}\n"
        f"Recommended containment steps (as checklist):\n{steps_formatted}"
    )

    response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    incident["report_template"] = response.get("report_template", "")

    return {"incident": incident}