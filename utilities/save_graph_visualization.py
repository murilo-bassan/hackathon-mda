from pathlib import Path
from core.graph_builder import graph
from utilities.logger_config import setup_logger
from utilities.config import GRAPH_PNG

logger = setup_logger(__name__)

def save_graph_visualization() -> None:
    
    logger.info("Gerando visualização do grafo...")

    png_data = graph.get_graph().draw_mermaid_png()

    output_path = Path(GRAPH_PNG)

    with open(output_path, "wb") as file:
        file.write(png_data)

    logger.info(f"Grafo salvo em: {output_path}")