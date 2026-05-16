from typing import TypedDict, Literal, NotRequired

class State(TypedDict, total=False):
    raw_input: dict
    input_type: Literal["request", "incident"]
    input_justification: str
    input_text: str
    result: dict
    ticket: dict
    response: dict
    closing_message: str
    incident: dict
    email: dict
