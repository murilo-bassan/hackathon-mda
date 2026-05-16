from process_incident.core.state.incident_state import State
from process_incident.utilities.config import CLASSIFY_CRITICALITY_PROMPT_PATH
from general_process.utilities.utils import call_llm
from general_process.utilities.prompt_loader import load_prompt

def classify_criticality(state: State) -> dict:
    """
    Classifica criticidade do incidente via LLM.
    """
    incident = state.get("incident", {})

    text = incident.get(
        "free_text",
        ""
    )
    system_prompt = load_prompt(CLASSIFY_CRITICALITY_PROMPT_PATH)
    user_prompt = f"""Incident report: {text}"""

    response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    incident["critical"] = response.get("critical", False)
    incident["critical_justification"] = response.get("justification", "")
    incident["category"] = response.get("category", "Indefinida")
    incident["category_justification"] = response.get("category_justification","")
    incident["scope"] = response.get("scope", "Indefinido")
    incident["affected_systems"] = response.get("affected_systems", "indefinido")

    return {"incident": incident}
