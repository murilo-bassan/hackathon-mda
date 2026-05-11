from typing import Optional, TypedDict

class Ticket(TypedDict):
    id: str
    timestamp: str
    channel: str
    requester_profile: str
    free_text: str

class Response(TypedDict):
    ticket_id: str #referência ao Ticket original
    category: str #"Incidente"
    urgency: int #5
    impact: int #5
    resulting_priority: int #4
    priority_justification: str #"Risco crítico identificado"
    service_type: str #"Suporte de Campo"
    support_level: int #2
    category_justification: str # "Falha em equipamento..."
    department: str # "N2 - Suporte de Campo"
    response_draft: str # "Olá Professor, registramos..."
    validation_status: bool = True # verifica se os dados foram validados corretamente ou não

# Definição inicial do estado do agente para o processo de atendimento de chamados de TIC, considerando todas as sugestões de etapas a serem automatizadas.
class State(TypedDict):
    # 1. PERMANENTES — existem do início ao fim
    ticket: Ticket
    '''current_ticket_index: int #qual ticket está sendo processado
    is_finished: bool'''
    closing_message: Optional[str]
    user_feedback: Optional[int]
    response: Response

    # 2. RESULTADOS DOS NÓS — preenchidos e lidos diretamente
    urgency: Optional[int] #score_priority → emit
    impact: Optional[int] #score_priority → emit
    service_type: Optional[str] #classify_type → emit
    support_level: Optional[int] #classify_type → emit
    category_justification: Optional[str] #classify_type → emit

    # 3. _current_* — temporários de coordenação entre nós
    '''_current_category: Optional[str]
    _current_department: Optional[str]
    _current_priority: Optional[int]
    _current_priority_justification: Optional[str]
    _current_draft: Optional[str]'''
