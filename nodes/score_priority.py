from state import State
from utilities.utils import call_llm

def score_priority(state: State) -> dict:
    ticket_text = state.get("free_text", "").lower()
    
    system_prompt = """
    Evaluate urgency and impact of an IT ticket.
    Values: 1 to 5 for urgency and impact.
    Resulting priority: 1 (Baixa), 2 (Media), 3 (Alta), 4 (Critica).
    Respond in JSON with keys: "urgency", "impact", "resulting_priority" and "priority_justification".
    """
    
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    partial = dict(state.get("response", {}))
    partial["urgency"] = response_data.get("urgency", 2)
    partial["impact"] = response_data.get("impact", 2)
    partial["resulting_priority"] = response_data.get("resulting_priority", 2)
    partial["priority_justification"] = response_data.get("priority_justification", "Calculado pela IA.")
    
    return {"response": partial}
