from langgraph.graph import END, START, StateGraph
import pandas as pd
from state import State
from nodes.ingest import ingest
from nodes.validation import validation
from nodes.classify_type import classify_type
from nodes.score_priority import score_priority
from nodes.route import route
from nodes.decide_response import decide_response
from nodes.validation_response import validation_response
from nodes.draft_response import draft_response
from nodes.emit import emit
from nodes.queue_only import queue_only

from IPython.display import Image, display

data = pd.read_json('data/data.json')

builder = StateGraph(State)

# Registro dos nós
builder.add_node("ingest", ingest)
builder.add_node("validation", validation)
builder.add_node("classify_type", classify_type)
builder.add_node("score_priority", score_priority)
builder.add_node("route", route)
builder.add_node("draft_response", draft_response)
builder.add_node("queue_only", queue_only)
builder.add_node("emit", emit)

# Arestas normais (fluxo sequencial principal)
builder.add_edge(START, "ingest")
builder.add_edge("ingest", "validation")

# Aresta condicional: após aditional_route, decide o próximo nó
builder.add_conditional_edges(
    "validation",
    validation_response,
    {
        "classify_type": "classify_type",
        "emit": "emit",
    }
)

builder.add_edge("classify_type", "score_priority")
builder.add_edge("score_priority", "route")

# Aresta condicional: após route, decide o próximo nó
builder.add_conditional_edges(
    "route",
    decide_response,
    {
        "draft_response": "draft_response",
        "queue_only": "queue_only",
    }
)

# draft_response sempre desemboca em emit
builder.add_edge("draft_response", "emit")
builder.add_edge("queue_only", "emit")
builder.add_edge("emit", END)

# Compilação do grafo
graph = builder.compile()

# Apresentação do grafo
png_data = graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(png_data)

""""
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

    # Chamada de cada call um a um
    for call in data:
        resultado = graph.invoke({"ticket": call})

        print("\n=== ESTADO FINAL ===")
        for campo, valor in resultado.items():
            print(f"  {campo}: {valor}")
"""