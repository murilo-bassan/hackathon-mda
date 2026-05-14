from state.state import State
from utilities.utils import call_llm
from utilities.config import VALIDATE_INPUT_PROMPT_PATH
from utilities.prompt_loader import load_prompt

def validate_input(state: State) -> dict:
    text = state.get("ticket", {}).get("free_text", "")

    system_prompt = load_prompt(VALIDATE_INPUT_PROMPT_PATH)

    response_data = call_llm(
        system_prompt, f"Please analyze the following ticket content and determine if it is valid and can be processed:\n\n\"{text}\""
    )

    partial = dict(state.get("ticket", {}))
    partial["needs_more_info"] = response_data.get("needs_more_info", False)
    partial["info_justification"] = response_data.get("info_justification", "")
    return {"ticket": partial}