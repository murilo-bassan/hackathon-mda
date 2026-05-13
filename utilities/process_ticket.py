from graph_builder import graph
from utilities.logger_config import setup_logger

logger = setup_logger(__name__)

def process_ticket(ticket_id: int, ticket: dict) -> None:

    logger.info("=" * 60)
    logger.info(f"Iniciando processamento do ticket {ticket_id}")

    try:
        response = graph.invoke({"ticket": ticket})
        logger.info("Processamento concluído com sucesso.")

        logger.info("=== RESPONSE ===")

        for key, value in response.items():
            logger.info(f"{key}: {value}")

    except Exception:
        logger.exception(
            f"Erro ao processar ticket {ticket_id}"
        )
