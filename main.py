from general_process.utilities.save_graph_visualization import save_graph_visualization
from process_request.utilities.load_tickets import load_tickets
from process_request.utilities.process_ticket import process_ticket
from process_request.utilities.accuracy import run_accuracy

def main() -> None:

    save_graph_visualization()

    tickets = load_tickets()

    START_INDEX = 20
    END_INDEX = 21

    for idx, ticket in enumerate(tickets, start=1):

        if idx <= START_INDEX:
            continue

        if idx > END_INDEX:
            break

        process_ticket(idx, ticket)


    run_accuracy()


if __name__ == "__main__":
    main()
