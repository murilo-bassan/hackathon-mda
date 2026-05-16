from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

DATA_PATH                        = BASE_DIR / "data" / "data.json"
QUEUE_PATH                       = BASE_DIR / "data" / "human_queue.json"
ARTIFACT_PATH                    = BASE_DIR / "artifacts"
DOC_PATH                         = BASE_DIR / "docs"
PROMPTS_PATH                     = BASE_DIR / "prompts"

GRAPH_PNG                        = DOC_PATH / "graph.png"
LOG_PATH                         = ARTIFACT_PATH / "logs"
RESPONSES_PATH                   = ARTIFACT_PATH / "responses_json"
REPORT_CSV                       = ARTIFACT_PATH / "report.csv"
CLASSIFY_PROMPT_PATH             = PROMPTS_PATH / "classify_type_prompt.md"
DRAFT_RESPONSE_PROMPT_PATH       = PROMPTS_PATH / "draft_response_prompt.md"
SCORE_IMPACT_PROMPT_PATH         = PROMPTS_PATH / "score_impact_prompt.md"
SCORE_URGENCY_PROMPT_PATH        = PROMPTS_PATH / "score_urgency_prompt.md"
JUSTIFY_PRIORITY_PROMPT_PATH     = PROMPTS_PATH / "justify_priority_prompt.md"
VALIDATE_INPUT_PROMPT_PATH       = PROMPTS_PATH / "validate_input_prompt.md"
DRAFT_REQUEST_PROMPT_PATH        = PROMPTS_PATH / "draft_request_prompt.md"