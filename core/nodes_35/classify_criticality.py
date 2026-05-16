from langchain_core.prompts import load_prompt
from core.state.state import State
from utilities.config import CLASSIFY_CRITICALITY_PROMPT_PATH
from utilities.utils import call_llm

def classify_criticality(state: State) -> dict:
    """
    Classifica criticidade do incidente via LLM.
    """
    incident = state.get("incident", {})

    text = incident.get(
        "normalized_text",
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

    return {"incident": incident}