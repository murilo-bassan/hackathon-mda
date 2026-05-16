from typing import TypedDict

from .incident import Incident
from .email import Email

class State(TypedDict):
    # Processo 3.5
    incident: Incident
    email: Email
