import logging
import sys
from pathlib import Path
from utilities.config import LOG_DIR

LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "execucao.log"

def setup_logger(name: str):
    logger = logging.getLogger(name)

    # Evita duplicar logs se a função for chamada duas vezes
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Handler 1: Salva no arquivo de log físico
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler 2: Mostra no Console/Terminal (O que a equipe pediu!)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger