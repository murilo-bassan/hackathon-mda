from core.state.state import State
from utilities.normalize import normalize_str


def decide_response_from_state(state: State) -> str:
    partial = state.get("response", {})

    priority = partial.get("resulting_priority", 99)
    category = partial.get("category", "")

    return decide_response(priority, category)


def decide_response(priority: int, category: str) -> str:
    if (
        (priority <= 3 and normalize_str(category) == "requisicao")
        or
        (priority <= 2 and normalize_str(category) == "incidente")
    ):
        return "draft_response"

    return "queue_only"