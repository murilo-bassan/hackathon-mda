from general_process.utilities.save_graph_visualization import save_graph_visualization
from general_process.utilities.load_input import load_input
from general_process.utilities.logger_config import setup_logger
from general_process.utilities.config import SHUFFLED_DATA_PATH
from process_request.utilities.accuracy import run_accuracy as acc_req
from process_incident.utilities.accuracy import run_accuracy as acc_inc

from general_process.utilities.process_ticket import process_ticket


logger = setup_logger(__name__)


def main(PATH: str) -> None:

    save_graph_visualization()

    tickets = load_input(PATH)

    START_INDEX = 0
    END_INDEX = 1
    
    for idx, ticket in enumerate(tickets, start=1):
        if idx <= START_INDEX:
            continue
        if idx > END_INDEX:
            break

        process_ticket(idx, ticket)

    error = acc_inc()
    error += acc_req()


    print("ERROS: ",error)


if __name__ == "__main__":
    main(SHUFFLED_DATA_PATH)
