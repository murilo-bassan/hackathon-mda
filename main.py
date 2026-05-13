import pandas as pd
from utilities.load_tickets import load_tickets
from utilities.save_graph_visualization import save_graph_visualization
from utilities.process_ticket import process_ticket

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


if __name__ == "__main__":
    main()