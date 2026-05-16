from typing import Optional, TypedDict, Annotated

from .ticket import Ticket
from .response import Response
from .incident import Incident
from .email import Email

"""
def merge_response(current: dict, update: dict) -> dict:
    return {**(current or {}), **(update or {})}
"""

class State(TypedDict):
    # 1. PERMANENTES — existem do início ao fim
    input_text: str
    
    # Processo 3.1
    ticket: Optional[Ticket]
    closing_message: Optional[str]
    response: Optional[Response]
    #response: Annotated[Response, merge_response]

    # Processo 3.5
    incident: Optional[Incident]
    email: Optional[Email]
