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
    '''current_ticket_index: int #qual ticket está sendo processado
    is_finished: bool'''
    closing_message: Optional[str]
    user_feedback: Optional[int]
    response: Response
    #response: Annotated[Response, merge_response]

    # 2. RESULTADOS DOS NÓS — preenchidos e lidos diretamente
    #urgency: Optional[int] #score_priority → emit
    #impact: Optional[int] #score_priority → emit
    #service_type: Optional[str] #classify_type → emit
    #support_level: Optional[int] #classify_type → emit
    #category_justification: Optional[str] #classify_type → emit

    # 3. _current_* — temporários de coordenação entre nós
    '''_current_category: Optional[str]
    _current_department: Optional[str]
    _current_priority: Optional[int]
    _current_priority_justification: Optional[str]
    _current_draft: Optional[str]'''
