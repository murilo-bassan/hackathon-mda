from typing import TypedDict

class Response(TypedDict):
    ticket_id: str #referência ao Ticket original
    category: str #"Incidente"
    urgency: int #5
    impact: int #5
    resulting_priority: int 
    priority_justification: str #"Risco crítico identificado"
    service_type: str #"Suporte de Campo"
    support_level: int #2
    category_justification: str # "Falha em equipamento..."
    department: str # "N2 - Suporte de Campo"
    response_draft: str # "Olá Professor, registramos..."
    validation_status: bool # verifica se os dados foram validados corretamente ou não