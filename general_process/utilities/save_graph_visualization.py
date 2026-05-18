from pathlib import Path
from general_process.core.graph_builder import get_compiled_graph
from general_process.utilities.logger_config import setup_logger
from general_process.utilities.config import GRAPH_PNG

logger = setup_logger(__name__)

def save_graph_visualization() -> None:
    
    logger.info("Gerando visualização do grafo...")

    graph = get_compiled_graph()
    png_data = graph.get_graph(xray=True).draw_mermaid_png()

    output_path = Path(GRAPH_PNG)

    output_path.parent.mkdir(parents=True, exist_ok=True) 

    with open(output_path, "wb") as file:
        file.write(png_data)

    logger.info(f"Grafo salvo em: {output_path}")
