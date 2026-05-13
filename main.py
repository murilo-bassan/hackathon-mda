from langgraph.graph import END, START, StateGraph
import pandas as pd
from state.state import State
from nodes.ingest import ingest
from nodes.classify_type import classify_type
from nodes.score_priority import score_priority
from utilities.decide_response import decide_response
from utilities.validation_response import validation_response
from nodes.draft_response import draft_response
from nodes.emit import emit
from nodes.queue_only import queue_only
from utilities.config import DATA_PATH, GRAPH_PNG
from utilities.logger_config import setup_logger

logger = setup_logger(__name__)

data = pd.read_json(DATA_PATH)

builder = StateGraph(State)

# Registro dos nós
builder.add_node("ingest", ingest)
builder.add_node("classify_type", classify_type)
builder.add_node("score_priority", score_priority)
builder.add_node("draft_response", draft_response)
builder.add_node("queue_only", queue_only)
builder.add_node("emit", emit)

# Arestas normais (fluxo sequencial principal)
builder.add_edge(START, "ingest")

# Aresta condicional: após validation, decide o próximo nó
builder.add_conditional_edges(
    "ingest",
    validation_response,
    {
        "classify_type": "classify_type",
        "emit": "emit",
    }
)

builder.add_edge("classify_type", "score_priority")

# Aresta condicional: após route, decide o próximo nó
builder.add_conditional_edges(
    "score_priority",
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

with open(GRAPH_PNG, "wb") as f:
    f.write(png_data)

if __name__ == "__main__":
    cont = 0
    for ticket in data.to_dict(orient="records"):
        cont+=1
        if (cont >=1 and cont <= 3):
            continue
        if(cont == 7):
            break

        logger.info("=" * 60)
        logger.info(f"Iniciando processamento do ticket {cont}")

        try:
            response = graph.invoke({"ticket": ticket})

            logger.info(f"Estado final: {response}")

            print("\n=== RESPONSE ===")
            for key, value in response.items():
                print(f"  {key}: {value}")

        except Exception as e:
            logger.exception(
                f"Erro ao processar ticket {cont}: {e}"
            )
            continue