# Decide, após o nó `route`, se o chamado vai para draft_response ou direto para emit 
from state import State

def decide_response(state: State) -> str:
    """
    Retorna o nome do próximo nó com base nas regras de negócio.
    
    if state["prioridade_resultante"] <= 2 and state["categoria"] == "requisição":
        print("[decide_response] → draft_response")
        return "draft_response"
    print("[decide_response] → queue_only")
    return "queue_only"
    """
    partial = state.get("response", {})
    prioridade = partial.get("resulting_priority", 99)
    categoria  = partial.get("category", "").strip().lower()

    if prioridade <= 2 and categoria == "requisição":
        print("[decide_response] → draft_response")
        return "draft_response"
    print("[decide_response] → queue_only")
    return "queue_only"