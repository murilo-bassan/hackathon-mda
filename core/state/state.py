from typing import TypedDict, Literal

class State(TypedDict):
    raw_input: dict
    input_type: Literal["request", "incident"]
    result: dict
