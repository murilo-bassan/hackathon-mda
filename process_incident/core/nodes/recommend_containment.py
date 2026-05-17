from process_incident.core.state.incident_state import State
from process_incident.utilities.config import RECOMMEND_CONTAINMENT_PROMPT_PATH, PLAYBOOK_PATH
from general_process.utilities.logger_config import setup_logger
from general_process.utilities.prompt_loader import load_prompt
from general_process.utilities.utils import call_llm

logger = setup_logger(__name__)

def _load_playbook() -> str:
    with open(PLAYBOOK_PATH, "r", encoding="utf-8") as f:
        return f.read()

def recommend_containment(state: State) -> dict:
    """
    Recomenda passos de contenção com base na categoria do incidente e no playbook.
    Usa LLM para selecionar e adaptar os passos mais relevantes.
    """
    incident = dict(state.get("incident", {}))

    category = incident.get("category", "other")
    critical = incident.get("critical", False)
    scope = incident.get("scope", "unknown")
    affected_systems = incident.get("affected_systems", "unknown")

    logger.info(f"Recomendando contenção para categoria: {category} | crítico: {critical}")

    playbook = _load_playbook()
    system_prompt = load_prompt(RECOMMEND_CONTAINMENT_PROMPT_PATH)

    user_prompt = (
        f"Incident category: {category}\n"
        f"Critical: {critical}\n"
        f"Scope: {scope}\n"
        f"Affected systems: {affected_systems}\n\n"
        f"Containment playbook:\n{playbook}"
    )

    response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    incident["containment_steps"] = response.get("containment_steps", [])
    incident["containment_justification"] = response.get("containment_justification", "")

    return {"incident": incident}