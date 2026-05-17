import json
from process_incident.utilities.config import INVENTORY_PATH

def load_inventory() -> list[dict]:
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)