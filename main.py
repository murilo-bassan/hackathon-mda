from langgraph.graph import END, START, StateGraph
from state import State
from nodes.flow import ingest, route, decide_response, draft_response, emit
from nodes.classify import classify_type
from nodes.score_priority import score_priority

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