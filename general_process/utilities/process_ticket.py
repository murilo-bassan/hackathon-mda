from general_process.utilities.logger_config import setup_logger

from general_process.core.graph_builder import get_compiled_graph

logger = setup_logger(__name__)

def process_ticket(ticket_id: int, ticket: dict) -> None:

    logger.info("=" * 60)
    logger.info(f"Iniciando processamento do ticket {ticket_id}")

    try:
        graph = get_compiled_graph()

        response = graph.invoke({"raw_input": ticket})
        logger.info("Processamento concluído com sucesso.")

        logger.info("=== RESPONSE ===")

        for key, value in response.items():
            logger.info(f"{key}: {value}")

    except Exception:
        logger.exception(
            f"Erro ao processar ticket {ticket_id}"
        )
