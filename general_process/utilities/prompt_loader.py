from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=None)
def load_prompt(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()