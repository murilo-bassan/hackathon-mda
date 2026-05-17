from typing import TypedDict

from .ticket import Ticket
from .response import Response

class State(TypedDict): 
    # Processo 3.1
    ticket: Ticket
    response: Response

RequestState = State
