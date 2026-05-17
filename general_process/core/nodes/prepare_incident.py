from general_process.core.state.state import State

def prepare_incident(state: State) -> dict:
    """
    Transforma o estado do grafo pai para o formato esperado
    pelo subgrafo de incidentes antes de entrar nele.
    """
    ticket = state.get("ticket") or {}
    return {
        "incident": {
            "id": ticket.get("id", ""),
            "timestamp": ticket.get("timestamp", ""),
            "free_text": state.get("input_text") or ticket.get("free_text", ""),
        }
    }