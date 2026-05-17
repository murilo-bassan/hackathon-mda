import pandas as pd
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

def load_input(data_path: str) -> list[dict]:
    logger.info(f"Carregando dados de: {data_path}")
    data = pd.read_json(data_path)
    input = data.to_dict(orient="records")
    logger.info(f"{len(input)} dados carregados.")
    return input