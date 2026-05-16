from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent

PROMPTS_PATH = BASE_DIR / "prompts"
CLASSIFY_INPUT_PROMPT_PATH = PROMPTS_PATH / "classify_input_prompt.md"

REQUEST_BASE_DIR = ROOT_DIR / "process_request"
ARTIFACT_PATH = REQUEST_BASE_DIR / "artifacts"
DOC_PATH = ROOT_DIR / "docs"
LOG_PATH = ARTIFACT_PATH / "logs"
GRAPH_PNG = DOC_PATH / "graph.png"
