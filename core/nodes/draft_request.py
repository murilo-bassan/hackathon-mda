from core.state.state import State
from utilities.utils import call_llm
from utilities.config import DRAFT_REQUEST_PROMPT_PATH
from utilities.prompt_loader import load_prompt

def draft_request(state: State) -> dict:
    text = state.get("ticket", {}).get("free_text", "")

    system_prompt = load_prompt(DRAFT_REQUEST_PROMPT_PATH)

    response_data = call_llm(
        system_prompt, f"Please analyze the following ticket content and draft a request:\n\n\"{text}\""
    )

    partial = dict(state.get("response", {}))
    partial["response_draft"] = response_data.get("response_draft", "")
    return {"response": partial}