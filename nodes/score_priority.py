from state.state import State
from utilities.utils import call_llm

def score_priority(state: State) -> dict:
    ticket = state.get("ticket", {})
    ticket_text = ticket.get("free_text", "")
    
    with open("prompts/score_priority_prompt.md", "r", encoding="utf-8") as file:
        system_prompt = file.read()
    
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    partial = dict(state.get("response", {}))
    partial["urgency"] = response_data.get("urgency", 2)
    partial["impact"] = response_data.get("impact", 2)
    partial["resulting_priority"] = response_data.get("resulting_priority", 2)
    partial["priority_justification"] = response_data.get("priority_justification", "Calculado pela IA.")
    
    return {"response": partial}
