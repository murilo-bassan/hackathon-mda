from general_process.core.state.state import State
from general_process.utilities.utils import call_llm
from general_process.utilities.prompt_loader import load_prompt
from general_process.utilities.config import CLASSIFY_INPUT_PROMPT_PATH

def classify_input(state: State) -> dict:
    raw_input = state.get("raw_input", {})
    text = raw_input.get("free_text", "")

    system_prompt = load_prompt(
        CLASSIFY_INPUT_PROMPT_PATH
    )

    user_prompt = f"""
    Texto:
    {text}
    """

    response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0
    )
    
    return {
        "input_type": response.get("input_type"), "input_justification": response.get("input_type_justification")}
