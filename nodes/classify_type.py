from state import State
from nodes.utils import call_llm

def classify_type(state: State) -> dict:
    system_prompt = """
    You are a Level 1 IT triage analyst. Classify the ticket.
    Categories: "Requisição", "Incidente" or "Problema".
    Respond EXCLUSIVELY in JSON with the keys: 
    - "categoria"
    - "tipo_servico"
    - "nivel_atendimento"
    - "justificativa_categoria"
    """
    
    ticket_text = state.get("txt_chamado", "")
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    return {
        "categoria": response_data.get("categoria", "Indefinida"),
        "tipo_servico": response_data.get("tipo_servico", "Geral"),
        "nivel_atendimento": response_data.get("nivel_atendimento", 1),
        "justificativa_categoria": response_data.get("justificativa_categoria", "Sem justificativa")
    }