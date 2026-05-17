from typing import TypedDict

from .incident import Incident

class State(TypedDict):
    # Processo 3.5
    incident: Incident

IncidentState = State
