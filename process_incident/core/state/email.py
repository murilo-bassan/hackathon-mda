from typing import TypedDict

class Email(TypedDict):
    criticality_header: str
    description: str
    evidence: str
    expected_deadline: str