from pathlib import Path
import pandas as pd
from utilities.config import DATA_PATH, GRAPH_PNG
from utilities.logger_config import setup_logger
from graph_builder import graph

logger = setup_logger(__name__)


def save_graph_visualization() -> None:
    
    logger.info("Gerando visualização do grafo...")

    png_data = graph.get_graph().draw_mermaid_png()

    output_path = Path(GRAPH_PNG)

    with open(output_path, "wb") as file:
        file.write(png_data)

    logger.info(f"Grafo salvo em: {output_path}")


def load_tickets() -> list[dict]:

    logger.info(f"Carregando dados de: {DATA_PATH}")
    data = pd.read_json(DATA_PATH)
    tickets = data.to_dict(orient="records")
    logger.info(f"{len(tickets)} tickets carregados.")

    return tickets


def process_ticket(ticket_id: int, ticket: dict) -> None:

    logger.info("=" * 60)
    logger.info(f"Iniciando processamento do ticket {ticket_id}")

    try:
        response = graph.invoke({"ticket": ticket})
        logger.info("Processamento concluído com sucesso.")

        print("\n=== RESPONSE ===")

        for key, value in response.items():
            print(f"{key}: {value}")

    except Exception:
        logger.exception(
            f"Erro ao processar ticket {ticket_id}"
        )


def main() -> None:

    save_graph_visualization()

    tickets = load_tickets()

    START_INDEX = 7
    END_INDEX = 8

    for idx, ticket in enumerate(tickets, start=1):

        if idx <= START_INDEX:
            continue

        if idx > END_INDEX:
            break

        process_ticket(idx, ticket)


if __name__ == "__main__":
    main()