from general_process.core.state.state import State
from general_process.utilities.normalize_text import normalize_text

def normalize_input(state: State) -> dict:
    """
    Normaliza texto para processamento pela IA.
    """

    raw_input = state.get("raw_input", {})
    raw_input_text = raw_input.get("free_text", "")

    raw_input["free_text"] = normalize_text(raw_input_text)

    return {
        "raw_input": raw_input
    }
