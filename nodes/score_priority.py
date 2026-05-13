from state.state import State
from utilities.utils import call_llm
from utilities.config import (
    SCORE_URGENCY_PROMPT_PATH,
    SCORE_IMPACT_PROMPT_PATH,
    JUSTIFY_PRIORITY_PROMPT_PATH
)
from utilities.prompt_loader import load_prompt

def score_priority(state: State) -> dict:
    ticket = state.get("ticket", {})
    ticket_text = ticket.get("free_text", "")
    partial = dict(state.get("response", {}))
    
    urgency_prompt = load_prompt(SCORE_URGENCY_PROMPT_PATH)
    urgency_response = call_llm(
        urgency_prompt,
        f"Ticket: {ticket_text}"
    )
    urgency = urgency_response.get("urgency", 2)

    impact_prompt = load_prompt(SCORE_IMPACT_PROMPT_PATH)
    impact_response = call_llm(
        impact_prompt,
        f"Ticket: {ticket_text}"
    )
    impact = impact_response.get("impact", 2)

    resulting_priority = max(
        1,
        min(5, (urgency * impact) // 5)
    )

    justification_prompt = load_prompt(
        JUSTIFY_PRIORITY_PROMPT_PATH
    )
    justification_response = call_llm(
        justification_prompt,
        f"""
        Ticket: {ticket_text}

        Urgency: {urgency}
        Impact: {impact}
        Resulting priority: {resulting_priority}
        """
    )
    priority_justification = justification_response.get("priority_justification", "Calculado pela IA.")
    
    partial["urgency"] = urgency
    partial["impact"] = impact
    partial["resulting_priority"] = resulting_priority
    partial["priority_justification"] = priority_justification
    
    return {"response": partial}
