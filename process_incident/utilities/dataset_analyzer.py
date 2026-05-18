from process_incident.utilities.analyzer import DatasetAnalyzer
from process_incident.utilities.config import DATA_PATH

def datasetAnalyzer():
    # instancia analisador do dataset
    analyzer = DatasetAnalyzer(DATA_PATH)

    print("=" * 60)
    print("\nANALISE DATASET\n")
    print("=" * 60)

    print("\nDistribuição de Categoria")
    print("-" * 25)
    print(analyzer.category_distribution())
    
    print("\nDistribuição de Criticidade")
    print("-" * 43)
    print(analyzer.critical_by_category())

    print("=" * 60) 
    print("\n")
