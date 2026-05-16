from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

PROMPTS_PATH                     = BASE_DIR / "prompts"
CLASSIFY_CRITICALITY_PROMPT_PATH = PROMPTS_PATH / "classify_criticality_prompt.md"
DRAFT_ALERT_PROMPT_PATH          = PROMPTS_PATH / "draft_alert_prompt.md"
INVENTORY_PATH                   = BASE_DIR / "data" / "inventory.json"
ARTIFACT_PATH                    = BASE_DIR / "artifacts"
RESPONSES_PATH                   = ARTIFACT_PATH / "responses_json"
REPORT_CSV                       = ARTIFACT_PATH / "report.csv"