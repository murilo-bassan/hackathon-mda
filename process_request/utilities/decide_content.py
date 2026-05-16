from process_request.core.state.request_state import State

def decide_content(state: State) -> str:
    partial = state.get("ticket", {})
    needs_more_info = partial.get("needs_more_info", False)

    if needs_more_info:
        return "draft_request"
    return "classify_type"