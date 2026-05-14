# Decide, após o nó `ingest`, se o chamado vai para draft_response ou direto para emit 
from state.state import State
import unicodedata

def normalize_str(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return s.encode("ascii", "ignore").decode().lower().strip()


def decide_response(state: State) -> str:
    """
    Retorna o nome do próximo nó com base nas regras de negócio.
    """
    partial = state.get("response", {})
    prioridade = partial.get("resulting_priority", 99)
    categoria  = partial.get("category", "").strip().lower()

    if prioridade <= 2 and normalize_str(categoria) == "requisicao":
        return "draft_response"
    return "queue_only"