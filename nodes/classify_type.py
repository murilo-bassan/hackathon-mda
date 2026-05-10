from state import State
from nodes.utils import call_llm

def classify_type(state: State) -> dict:
    system_prompt = """
    You are a Level 1 IT triage analyst. Classify the ticket.
    Categories: "Requisição", "Incidente" or "Problema".
    Respond EXCLUSIVELY in JSON with the keys: 
    - "category"
    - "service_type"
    - "support_level"
    - "category_justification"
    """
    
    ticket_text = state.get("free_text", "")
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")

    #inserir dados de "treinamento" para a LLM few shot
    
    return {
        "category": response_data.get("category", "Indefinida"),
        "service_type": response_data.get("service_type", "Geral"),
        "support_level": response_data.get("support_level", 1),
        "category_justification": response_data.get("category_justification", "Sem justificativa")
    }