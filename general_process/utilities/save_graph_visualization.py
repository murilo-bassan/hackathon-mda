from pathlib import Path
from general_process.core.graph_builder import graph
from general_process.utilities.logger_config import setup_logger
from general_process.utilities.config import GRAPH_PNG

logger = setup_logger(__name__)

def save_graph_visualization() -> None:
    
    logger.info("Gerando visualização do grafo...")

    png_data = graph.get_graph(xray=True).draw_mermaid_png()

    output_path = Path(GRAPH_PNG)

    output_path.parent.mkdir(parents=True, exist_ok=True) 

    with open(output_path, "wb") as file:
        file.write(png_data)

    logger.info(f"Grafo salvo em: {output_path}")
