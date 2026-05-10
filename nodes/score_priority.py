from state import State
from nodes.utils import call_llm

def score_priority(state: State) -> dict:
    ticket_text = state.get("free_text", "").lower()
    
    critical_words = ['caiu', 'servidor', 'vazamento', 'hacker', 'parou']
    
    if any(word in ticket_text for word in critical_words):
        return {
            "urgency": 5,
            "impact": 5,
            "resulting_priority": 4,
            "priority_justification": "Regra deterministica: Risco critico identificado."
        }
        
    system_prompt = """
    Evaluate urgency and impact of an IT ticket.
    Values: 1 to 5 for urgency and impact.
    Resulting priority: 1 (Baixa), 2 (Media), 3 (Alta), 4 (Critica).
    Respond in JSON with keys: "urgency", "impact", "resulting_priority" and "priority_justification".
    """
    
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    return {
        "urgency": response_data.get("urgency", 2),
        "impact": response_data.get("impact", 2),
        "resulting_priority": response_data.get("resulting_priority", 2),
        "priority_justification": response_data.get("priority_justification", "Calculado pela IA.")
    }