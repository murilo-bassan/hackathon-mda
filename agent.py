from typing import Optional, TypedDict
from langgraph.graph import StateGraph

# Definição inicial do estado do agente para o processo de atendimento de chamados de TIC, considerando todas as sugestões de etapas a serem automatizadas.
class State(TypedDict):
    #etapa 1 (identificação e priorização)
    txt_chamado: str
    urgencia: int #com base em palavras-chave, sistemas afetados e perfil do solicitante
    impacto: int #com base em palavras-chave, sistemas afetados e perfil do solicitante
    prioridade_resultante: int
    justificativa_prioridade: str 

    #etapa 2 (Categorização e escalonamento)
    categoria: str #requisição, incidente ou problema
    tipo_servico: str #a partir do catalogo de de TIC
    nivel_atendimento: int #1, 2 ou 3
    justificativa_categoria: str
    setor: str

    #etapa 3 (Resposta inicial automatizada) - chamados de baixa complexidade
    rascunho_resposta: str #com base em uma ___base de conhecimento sintética___ para revisão do analista

    #etapa 4 (Notificação de encerramento)
    finalizado: bool
    mensagem_encerramento: Optional[str]
    feedback_usuario: int #satisfação do usuário (de 1 a 5)

