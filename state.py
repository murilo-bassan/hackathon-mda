from typing import List, Optional, TypedDict

class Ticket(TypedDict):
    id: str
    timestamp: str
    channel: str
    requester_profile: str
    free_text: str

class Response(TypedDict):
    ticket_id: str
    category: str
    resulting_priority: int
    priority_justification: str 
    department: str
    response_draft: str

# Definição inicial do estado do agente para o processo de atendimento de chamados de TIC, considerando todas as sugestões de etapas a serem automatizadas.
class State(TypedDict):
    #etapa 1 (identificação e priorização)
    tickets: List[Ticket] #fila de chamados a serem processados
    urgency: int #com base em palavras-chave, sistemas afetados e perfil do solicitante
    impact: int #com base em palavras-chave, sistemas afetados e perfil do solicitante

    #etapa 2 (Categorização e escalonamento)
    #category: str #requisição, incidente ou problema
    service_type: str #a partir do catalogo de de TIC
    support_level: int #1, 2 ou 3
    category_justification: str

    #etapa 3 (Resposta inicial automatizada) - chamados de baixa complexidade

    #etapa 4 (Notificação de encerramento)
    is_finished: bool
    closing_message: Optional[str]
    user_feedback: int #satisfação do usuário (de 1 a 5)
    responses: List[Response] #histórico de respostas geradas para cada ticket, incluindo rascunhos e mensagens de encerramento