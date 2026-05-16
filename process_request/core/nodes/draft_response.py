from process_request.core.state.request_state import State
from general_process.utilities.utils import call_llm
from process_request.utilities.build_few_shot import build_few_shot
from process_request.utilities.config import DRAFT_RESPONSE_PROMPT_PATH
from general_process.utilities.prompt_loader import load_prompt

def draft_response(state: State) -> dict:
    ticket = state.get("ticket", {})
    department = state.get("response", {}).get("department", "")
    few_shot = build_few_shot(department)

    system_prompt = load_prompt(DRAFT_RESPONSE_PROMPT_PATH)

    response_data = call_llm(
        system_prompt,
        f"Examples:\n{few_shot}\n\nNow respond to: \"{ticket.get('free_text', '')}\""
    )

    partial = dict(state.get("response", {}))
    partial["response_draft"] = response_data.get("response_draft", "")
    return {"response": partial}