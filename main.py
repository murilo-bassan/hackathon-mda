from general_process.utilities.save_graph_visualization import save_graph_visualization
from process_request.utilities.load_tickets import load_tickets
from process_request.utilities.process_ticket import process_ticket
from process_request.utilities.accuracy import run_accuracy
from process_request.utilities.analyzer import DatasetAnalyzer
from process_request.utilities.config import DATA_PATH


def main() -> None:

    datasetAnalyzer()

    save_graph_visualization()

    tickets = load_tickets()

    START_INDEX = 0
    END_INDEX = 1

    for idx, ticket in enumerate(tickets, start=1):

        if idx <= START_INDEX:
            continue

        if idx > END_INDEX:
            break

        process_ticket(idx, ticket)


    errors = run_accuracy()

    print("\nTICKET COM PRIORIDADE DIFERENTE (",len(errors),"):")
    for i in errors:
        print(i)

def datasetAnalyzer():
    # instancia analisador do dataset
    analyzer = DatasetAnalyzer(DATA_PATH)

    print("=" * 60)
    print("ANALISE DATASET")

    print("\n Distribuição de Categoria")
    print(analyzer.category_distribution())
    print("\n Distribuição de Prioridade")
    print(analyzer.priority_by_category())

    print("=" * 60) 
    print("\n")

if __name__ == "__main__":
    main()
