from main import main
from process_incident.utilities.accuracy import run_accuracy
from process_incident.utilities.config import DATA_PATH
from process_incident.utilities.dataset_analyzer import datasetAnalyzer

if __name__ == "__main__":
    datasetAnalyzer()
    
    main(DATA_PATH)

    run_accuracy()
