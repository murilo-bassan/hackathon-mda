from state import State, Ticket

def ingest(state: State) -> dict:
    """
    Valida o JSON de entrada e normaliza o texto.
    """
    # Resgata sempre a primeira entrada do JSON, com a intenção de deletar ela depois
    raw_ticket = None;
    
    # verificar se o chamado esta vazio
    if not raw_ticket:
        return {}
    

    # checar se todas os campos existem?
    
    # verificar se o free_text esta vazio (ja que todo o processamento depende dele)
    if not raw_ticket["free_text"]:
        return {}
    
    # Limpa o free_text
    clean_text =  " ".join((raw_ticket["free_text"]).lower().strip().split())
    
    # mais metodos de limpar o texto?

    # chamar uma LLM para arrumar erros ortográficos para melhorar o desempenho dos categorizadores?

    # Atualiza o campo com o clean_text
    normalized_text: Ticket = {
        "id": raw_ticket["id"],
        "timestamp": raw_ticket["timestamp"],
        "channel": raw_ticket["channel"],
        "requester_profile": raw_ticket["requester_profile"],
        "free_text": clean_text
    }
    
    return {"ticket": [normalized_text]}
