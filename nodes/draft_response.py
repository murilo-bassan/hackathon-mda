from state.state import State
from utilities.utils import call_llm
from utilities.build_few_shot import build_few_shot
from utilities.config import DRAFT_RESPONSE_PROMPT_PATH

def draft_response(state: State) -> dict:
    ticket = state.get("ticket", {})
    department = state.get("response", {}).get("department", "")
    few_shot = build_few_shot(department)

    with open(DRAFT_RESPONSE_PROMPT_PATH, "r", encoding="utf-8") as file:
        system_prompt = file.read()

    response_data = call_llm(
        system_prompt,
        f"Examples:\n{few_shot}\n\nNow respond to: \"{ticket.get('free_text', '')}\""
    )

    partial = dict(state.get("response", {}))
    partial["response_draft"] = response_data.get("response_draft", "")
    return {"response": partial}