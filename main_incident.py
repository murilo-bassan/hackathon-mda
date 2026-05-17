from general_process.utilities.save_graph_visualization import save_graph_visualization
from general_process.utilities.load_input import load_input
from general_process.core.graph_builder import graph
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

def main() -> None:
    save_graph_visualization()

    incidents = load_input("process_incident/data/incidents.json")

    START_INDEX = 0
    END_INDEX = 1

    for idx, incident in enumerate(incidents, start=1):
        if idx <= START_INDEX:
            continue
        if idx > END_INDEX:
            break

        logger.info(f"Processando incidente {idx}")
        try:
            response = graph.invoke({
                "ticket": incident,
                "input_type": "incident"  # ← força o roteamento
            })
            logger.info(f"Concluído: {response}")
        except Exception:
            logger.exception(f"Erro ao processar incidente {idx}")

if __name__ == "__main__":
    main()