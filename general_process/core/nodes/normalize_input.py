from general_process.core.state.state import State
from general_process.utilities.normalize_text import normalize_text

def normalize_input(state: State) -> dict:
    """
    Normaliza texto para processamento pela IA.
    """

    raw_input_text = state.get("input_text", "")

    normalized_input_text = normalize_text(raw_input_text)

    return {"input_text": normalized_input_text}
