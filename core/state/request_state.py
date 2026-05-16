from typing import TypedDict, Optional

from .ticket import Ticket
from .response import Response

class State(TypedDict): 
    # Processo 3.1
    ticket: Ticket
    closing_message: Optional[str]
    response: Response
