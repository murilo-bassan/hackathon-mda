from state import State
from nodes.utils import call_llm

def score_priority(state: State) -> dict:
    ticket_text = state.get("txt_chamado", "").lower()
    
    critical_words = ['caiu', 'servidor', 'vazamento', 'hacker', 'parou']
    
    if any(word in ticket_text for word in critical_words):
        return {
            "urgencia": 5,
            "impacto": 5,
            "prioridade_resultante": 4,
            "justificativa_prioridade": "Regra deterministica: Risco critico identificado."
        }
        
    system_prompt = """
    Evaluate urgency and impact of an IT ticket.
    Values: 1 to 5 for urgency and impact.
    Resulting priority: 1 (Baixa), 2 (Media), 3 (Alta), 4 (Critica).
    Respond in JSON with keys: "urgencia", "impacto", "prioridade_resultante" and "justificativa_prioridade".
    """
    
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    return {
        "urgencia": response_data.get("urgencia", 2),
        "impacto": response_data.get("impacto", 2),
        "prioridade_resultante": response_data.get("prioridade_resultante", 2),
        "justificativa_prioridade": response_data.get("justificativa_prioridade", "Calculado pela IA.")
    }