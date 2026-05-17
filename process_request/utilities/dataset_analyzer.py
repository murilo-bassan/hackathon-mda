from process_request.utilities.analyzer import DatasetAnalyzer
from process_request.utilities.config import DATA_PATH

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
