from state.state import State
from utilities.utils import call_llm

def classify_type(state: State) -> dict:
    # A variável abaixo guarda todo o manual de instruções e os exemplos
    with open("prompts/classify_type_prompt.md", "r", encoding="utf-8") as file:
        system_prompt = file.read()
    
    # Aqui o código pega o texto do chamado do usuário
    ticket_text = state.get("ticket", {}).get("free_text", "")
    
    # Aqui nós disparamos as instruções (com os exemplos) + o chamado do usuário para a IA
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    # Retornamos a resposta formatada para o LangGraph
    partial = dict(state.get("response", {}))
    partial["ticket_id"] = state["ticket"]["id"]
    partial["category"] = response_data.get("category", "Indefinida")
    partial["service_type"] = response_data.get("service_type", "Geral")
    partial["support_level"] = response_data.get("support_level", 1)
    partial["category_justification"] = response_data.get("category_justification", "Sem justificativa")
    partial["department"] = response_data.get("department", "Geral")
    
    return {"response": partial}