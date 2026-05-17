from process_incident.core.state.incident_state import State
from general_process.utilities.logger_config import setup_logger
from process_incident.utilities.config import DRAFT_ALERT_PROMPT_PATH
from general_process.utilities.prompt_loader import load_prompt
from general_process.utilities.utils import call_llm

logger = setup_logger(__name__)

def draft_alert(state: State) -> dict:
    """
    Gera o e-mail de alerta para o responsável técnico identificado.
    O tom e a urgência variam conforme a criticidade do incidente.
    """
    incident = dict(state.get("incident", {}))

    responsible_person = incident.get("responsible_person", "Responsável Técnico")
    contact_info = incident.get("contact_info", "")
    category = incident.get("category", "other")
    critical = incident.get("critical", False)
    scope = incident.get("scope", "unknown")
    affected_systems = incident.get("affected_systems", "unknown")
    containment_steps = incident.get("containment_steps", [])
    free_text = incident.get("free_text", "")

    logger.info(f"Redigindo alerta para: {responsible_person} | crítico: {critical}")

    system_prompt = load_prompt(DRAFT_ALERT_PROMPT_PATH)

    steps_formatted = "\n".join(
        f"- {step}" for step in containment_steps
    ) or "- Aguardando recomendação de contenção."

    user_prompt = (
        f"Responsible person name: {responsible_person}\n"
        f"Contact info: {contact_info}\n"
        f"Incident category: {category}\n"
        f"Critical: {critical}\n"
        f"Scope: {scope}\n"
        f"Affected systems: {affected_systems}\n"
        f"Original incident report: {free_text}\n"
        f"Recommended containment steps:\n{steps_formatted}"
    )

    response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    incident["alert_draft"] = response.get("alert_draft", "")

    return {"incident": incident}