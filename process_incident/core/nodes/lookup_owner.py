from process_incident.core.state.incident_state import State
from general_process.utilities.logger_config import setup_logger
from process_incident.utilities.find_owner import find_owner
from process_incident.utilities.load_inventory import load_inventory

logger = setup_logger(__name__)

def lookup_owner(state: State) -> dict:
    """
    Busca determinística do responsável técnico pelo sistema afetado.
    Não usa LLM — cruza o campo affected_systems com o inventário sintético.
    """
    incident = dict(state.get("incident", {}))

    affected_systems = incident.get("affected_systems", "unknown")

    logger.info(f"Buscando responsável para sistemas: {affected_systems}")

    inventory = load_inventory()
    owner = find_owner(affected_systems, inventory)

    incident["responsible_person"] = owner["responsible_person"]
    incident["contact_info"] = owner["contact_info"]

    logger.info(f"Responsável identificado: {owner['responsible_person']}")

    return {"incident": incident}