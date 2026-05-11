# Decide, após o nó `route`, se o chamado vai para draft_response ou direto para emit 
from state import State

def validation_response(state: State) -> str:
    """
    Retorna o nome do próximo nó com base nas regras de negócio.
    
    if state["prioridade_resultante"] <= 2 and state["categoria"] == "requisição":
        print("[decide_response] → draft_response")
        return "draft_response"
    print("[decide_response] → emit (enfileirado para humano)")
    return "emit"
    """
    prioridade = state["tickets"][state["current_ticket_index"]]["resulting_priority"]
    categoria = state["tickets"][state["current_ticket_index"]]["category"].strip().lower()

    if prioridade <= 4 and categoria == "requisição":
        print("[decide_response] → draft_response")
        return "draft_response"
    print("[decide_response] → emit (enfileirado para humano)") #queue_only
    return "emit"