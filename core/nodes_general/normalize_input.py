from core.state.state import State
from utilities.normalize_text import normalize_text

def normalize_input(state: State) -> dict:
    """
    Normaliza texto para processamento pela IA.
    """

    ticket = dict(state.get("ticket", {}))

    raw_text = ticket.get("free_text", "")

    normalized_text = normalize_text(raw_text)

    ticket["raw_text"] = raw_text
    ticket["normalized_text"] = normalized_text

    return {"ticket": ticket}