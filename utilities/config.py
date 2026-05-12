from pathlib import Path

BASE_DIR = Path(__file__).parent

DATA_PATH               = BASE_DIR / "data" / "data.json"
QUEUE_PATH              = BASE_DIR / "data" / "human_queue.json"
RESPONSES_DIR           = BASE_DIR / "responses_json"
REPORT_CSV              = BASE_DIR / "report.csv"
GRAPH_PNG               = BASE_DIR / "graph.png"
PROMPTS_DIR             = BASE_DIR / "prompts"
CLASSIFY_PROMPT_PATH    = PROMPTS_DIR / "classify_type_prompt.md"
SCORE_PROMPT_PATH       = PROMPTS_DIR / "score_priority_prompt.md"
DRAFT_RESPONSE_PROMPT_PATH = PROMPTS_DIR / "draft_response_prompt.md"