# Após o nó `validation`, encaminha conforme o resultado do ingest (via `response`).
from state.state import State

def validation_response(state: State) -> str:
    """
    Se o ingest marcou falha de validação, vai direto para emit; caso contrário segue o fluxo.
    """
    resp = state.get("response") or {}
    
    if resp.get("validation_status") is False:
        return "emit"
    
    return "classify_type"