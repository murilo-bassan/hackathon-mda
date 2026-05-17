from typing import TypedDict, Literal

class State(TypedDict, total=False):
    raw_input: dict
    input_type: Literal["request", "incident"]
    input_justification: str
    result: dict
