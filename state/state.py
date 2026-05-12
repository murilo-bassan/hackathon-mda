from typing import Optional, TypedDict, Annotated

from .ticket import Ticket
from .response import Response

"""
def merge_response(current: dict, update: dict) -> dict:
    return {**(current or {}), **(update or {})}
"""

# Definição inicial do estado do agente para o processo de atendimento de chamados de TIC, considerando todas as sugestões de etapas a serem automatizadas.
class State(TypedDict):
    # 1. PERMANENTES — existem do início ao fim
    ticket: Ticket
    closing_message: Optional[str]
    user_feedback: Optional[int]
    response: Response
    #response: Annotated[Response, merge_response]
