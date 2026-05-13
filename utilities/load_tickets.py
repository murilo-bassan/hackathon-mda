import pandas as pd
from utilities.config import DATA_PATH
from utilities.logger_config import setup_logger

logger = setup_logger(__name__)

def load_tickets() -> list[dict]:

    logger.info(f"Carregando dados de: {DATA_PATH}")
    data = pd.read_json(DATA_PATH)
    tickets = data.to_dict(orient="records")
    logger.info(f"{len(tickets)} tickets carregados.")

    return tickets