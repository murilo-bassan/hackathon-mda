from core.state.state import State
from utilities.utils import call_llm
from utilities.prompt_loader import load_prompt
from utilities.config import CLASSIFY_INPUT_PROMPT_PATH

def classify_input(state: State) -> dict:

    ticket = state.get("ticket", {})

    text = ticket.get("normalized_text", "")

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
    
    return {"input_type": response.get("input_type"), "input_justification": response.get("justification")}