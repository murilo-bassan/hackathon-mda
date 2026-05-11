import json
from state import State
from nodes.utils import call_llm

with open("data/data.json", "r", encoding="utf-8") as f:
    tickets_kb = json.load(f)

def _build_few_shot(department: str, n: int = 3) -> str:
    exemplos = [
        t for t in tickets_kb
        if t.get("suggested_sector") == department
        and t.get("draft_response")
    ]
    if not exemplos:
        exemplos = [t for t in tickets_kb if t.get("draft_response")]

    few_shot = ""
    for t in exemplos[:n]:
        few_shot += (
            f"Ticket: \"{t['free_text']}\"\n"
            f"Response: \"{t['draft_response']}\"\n\n"
        )
    return few_shot.strip()

def draft_response(state: State) -> dict:
    ticket = state["ticket"]
    department = state.get("response", {}).get("department", "")
    few_shot = _build_few_shot(department)

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