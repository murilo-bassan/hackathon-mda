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

#nós comentados (serão feitos em arquivos diferentes e posteiormente importados aqui para compor o grafo final)
"""
def ingest(state: State) -> dict:
    
    Valida o JSON de entrada e normaliza o texto.
    
    print("[ingest] Chamado recebido:", state["txt_chamado"][:60], "...")
    return {}


def classify_type(state: State) -> dict:
    
    LLM com few-shot, retornando { Requisição | Incidente | Problema }
    com justificativa.
    
    print("[classify_type] Classificando chamado...")
    return {
        "categoria": "requisição",
        "tipo_servico": "acesso_sistema",
    }


def score_priority(state: State) -> dict:
    
    Calcula urgência, impacto e prioridade resultante.
    Combina LLM (análise de contexto) com regras determinísticas
    para garantir explicabilidade.
    
    print("[score_priority] Calculando prioridade...")
    return {
        "urgencia": 2,
        "impacto": 2,
        "prioridade_resultante": 2,
    }


def route(state: State) -> dict:
    
    Função pura que mapeia (categoria, prioridade, tipo de serviço) → setor da
    AGETIC.
    
    print("[route] Roteando chamado...")
    return {
        "nivel_atendimento": 1,
    }


def draft_response(state: State) -> dict:
    
    LLM consulta base de conhecimento sintética e produz rascunho
    de e-mail.
    
    print("[draft_response] Gerando rascunho de resposta...")
    return {
        "rascunho_resposta": "Rascunho",
    }


def emit(state: State) -> dict:
    
    Serializa a saída final e registra log estruturado.
    
    print("[emit] Emitindo resultado final...")
    return {
        "finalizado": True,
        "mensagem_encerramento": "Seu chamado foi processado. Em breve você receberá um retorno.",
        "feedback_usuario": 0, 
    }
"""

# Decide, após o nó `route`, se o chamado vai para draft_response ou direto para emit 
def decide_response(state: State) -> str:
    """
    Retorna o nome do próximo nó com base nas regras de negócio.
    """
    if state["prioridade_resultante"] <= 2 and state["categoria"] == "requisição":
        print("[decide_response] → draft_response")
        return "draft_response"
    print("[decide_response] → emit (enfileirado para humano)")
    return "emit"

builder = StateGraph(State)

# Registro dos nós
builder.add_node("ingest", ingest)
builder.add_node("classify_type", classify_type)
builder.add_node("score_priority", score_priority)
builder.add_node("route", route)
builder.add_node("draft_response", draft_response)
builder.add_node("emit", emit)

# Arestas normais (fluxo sequencial principal)
builder.add_edge(START, "ingest")
builder.add_edge("ingest", "classify_type")
builder.add_edge("classify_type", "score_priority")
builder.add_edge("score_priority", "route")

# Aresta condicional: após route, decide o próximo nó
builder.add_conditional_edges(
    "route",
    decide_response,
    {
        "draft_response": "draft_response",
        "emit": "emit",
    }
)

# draft_response sempre desemboca em emit
builder.add_edge("draft_response", "emit")
builder.add_edge("emit", END)

# Compilação do grafo
graph = builder.compile()


if __name__ == "__main__":
    chamado_exemplo = {
        "txt_chamado": "Não consigo acessar o sistema de e-mail institucional desde hoje cedo.",
        "urgencia": 0,
        "impacto": 0,
        "prioridade_resultante": 0,
        "categoria": "",
        "tipo_servico": "",
        "nivel_atendimento": 0,
        "rascunho_resposta": "",
        "finalizado": False,
        "mensagem_encerramento": "",
        "feedback_usuario": 0,
    }

    resultado = graph.invoke(chamado_exemplo)

    print("\n=== ESTADO FINAL ===")
    for campo, valor in resultado.items():
        print(f"  {campo}: {valor}")
