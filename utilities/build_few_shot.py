import json
from state import State

with open("data/data.json", "r", encoding="utf-8") as f:
    tickets_kb = json.load(f)

def build_few_shot(department: str, n: int = 3) -> str:
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