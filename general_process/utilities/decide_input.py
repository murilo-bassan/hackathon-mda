from general_process.core.state.state import State

from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

VALID_INPUT_TYPES = {"request", "incident"}

def decide_input(state: State) -> str:
    """
    Decide which workflow to execute based on the classified input type.
    """

    input_type = state.get("input_type")

    if input_type not in VALID_INPUT_TYPES:
        logger.error(
            f"input_type inválido ou ausente: '{input_type}'. "
            "Verifique a saída do nó classify_input."
        )

        # Fail-safe explícito: escalar para o fluxo mais conservador
        return "incident"
    
    return input_type
