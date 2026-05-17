from main import main

from process_request.utilities.accuracy import run_accuracy
from process_request.utilities.dataset_analyzer import datasetAnalyzer
from process_request.utilities.config import DATA_PATH


if __name__ == "__main__":
    datasetAnalyzer()

    main(DATA_PATH)

    errors = run_accuracy()
    print("\nTICKET COM PRIORIDADE DIFERENTE (", len(errors), "):")
    for i in errors:
        print(i)
