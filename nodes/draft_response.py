from state.state import State
from utilities.utils import call_llm
from utilities.build_few_shot import build_few_shot

def draft_response(state: State) -> dict:
    ticket = state["ticket"]
    department = state.get("response", {}).get("department", "")
    few_shot = build_few_shot(department)

    system_prompt = """
    You are a Level 1 IT analyst at AGETIC/UFMS.
    Write a response email in Brazilian Portuguese: cordial, objective, max 120 words.
    Base your response ONLY on the ticket and the examples provided.
    Respond with a JSON with the key "response_draft".
    """

    response_data = call_llm(
        system_prompt,
        f"Examples:\n{few_shot}\n\nNow respond to: \"{ticket['free_text']}\""
    )

    partial = dict(state.get("response", {}))
    partial["response_draft"] = response_data.get("response_draft", "")
    return {"response": partial}