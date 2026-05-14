"""
conftest.py — Configuração Compartilhada do pytest
===================================================
Projeto : Triagem de Chamados de TIC (AGETIC/UFMS)

Este arquivo é carregado automaticamente pelo pytest antes de qualquer
test_*.py. Ele garante que o sys.path aponte para a raiz do projeto,
permitindo importações relativas como `from nodes.ingest import ingest`
sem precisar instalar o pacote.

Como usar:
  Coloque este conftest.py na pasta `tests/` (irmã do código-fonte)
  OU na raiz do projeto.

Estrutura esperada:
  projeto/
  ├── conftest.py         ← este arquivo (coloque na raiz ou em tests/)
  ├── nodes/
  ├── utilities/
  ├── state/
  ├── prompts/
  └── tests/
      ├── test_nodes.py
      └── test_edges.py
"""

import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Garante que a raiz do projeto esteja no sys.path
# ─────────────────────────────────────────────────────────────────────────────

# Detecta a raiz do projeto (pasta que contém `nodes/`, `utilities/`, etc.)
# Sobe um nível a partir do conftest.py se ele estiver em tests/
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent if _HERE.name == "tests" else _HERE

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# Variáveis de ambiente para testes (evita dependência de .env)
# ─────────────────────────────────────────────────────────────────────────────

os.environ.setdefault("OPENROUTER_API_KEY", "test-key-mocked")
os.environ.setdefault("MODEL_NAME", "test-model")
