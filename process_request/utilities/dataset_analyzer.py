from process_request.utilities.analyzer import DatasetAnalyzer
from process_request.utilities.config import DATA_PATH

def datasetAnalyzer():
    # instancia analisador do dataset
    analyzer = DatasetAnalyzer(DATA_PATH)

    print("=" * 60)
    print("\nANALISE DATASET\n")
    print("=" * 60)

    print("\nDistribuição de Categoria")
    print("-" * 25)
    print(analyzer.category_distribution())
    
    print("\nDistribuição de Prioridade")
    print("-" * 43)
    print(analyzer.priority_by_category())

    print("=" * 60) 
    print("\n")
