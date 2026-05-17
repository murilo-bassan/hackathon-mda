from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent

PROMPTS_PATH = BASE_DIR / "prompts"
CLASSIFY_INPUT_PROMPT_PATH = PROMPTS_PATH / "classify_input_prompt.md"

REQUEST_BASE_DIR = ROOT_DIR / "process_request"
INCIDENT_BASE_DIR = ROOT_DIR / "process_incident"

ARTIFACT_PATH = REQUEST_BASE_DIR / "artifacts"
DOC_PATH = ROOT_DIR / "docs"
LOG_PATH = ARTIFACT_PATH / "logs"
GRAPH_PNG = DOC_PATH / "graph.png"

DATA_REQUEST_PATH = REQUEST_BASE_DIR / "data" / "data.json"
DATA_INCIDENT_PATH = INCIDENT_BASE_DIR / "data" / "incidents.json"

SHUFFLED_DATA_PATH = BASE_DIR / "data" / "shuffled_data.json"