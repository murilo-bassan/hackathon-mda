from typing import TypedDict

class Ticket(TypedDict):
    id: str
    timestamp: str
    channel: str
    requester_profile: str
    free_text: str