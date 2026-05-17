from general_process.utilities.save_graph_visualization import save_graph_visualization
from process_request.utilities.accuracy import run_accuracy
from general_process.core.graph_builder import graph
from general_process.utilities.logger_config import setup_logger
from utilities.load_input import load_input

logger = setup_logger(__name__)

def main() -> None:
    save_graph_visualization()

    tickets = load_input("process_request/data/data.json") # carrega process_request/data/data.json

    START_INDEX = 0
    END_INDEX = 1

    for idx, ticket in enumerate(tickets, start=1):
        if idx <= START_INDEX:
            continue
        if idx > END_INDEX:
            break

        logger.info(f"Processando request {idx}")
        try:
            response = graph.invoke({
                "ticket": ticket,
                "input_type": "request"  # ← força o roteamento
            })
            logger.info(f"Concluído: {response}")
        except Exception:
            logger.exception(f"Erro ao processar ticket {idx}")

    errors = run_accuracy()
    print("\nTICKET COM PRIORIDADE DIFERENTE (", len(errors), "):")
    for i in errors:
        print(i)

if __name__ == "__main__":
    main()