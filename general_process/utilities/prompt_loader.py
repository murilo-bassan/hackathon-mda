from functools import lru_cache
from pathlib import Path

import os

def load_prompt(path: Path) -> str:
    """Cache habilitado apenas em produção via variável de ambiente."""
    if os.getenv("CACHE_PROMPTS", "false").lower() == "true":
        return _load_prompt_cached(path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@lru_cache(maxsize=64)
def _load_prompt_cached(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
