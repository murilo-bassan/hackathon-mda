"""
conftest.py — Configuração Compartilhada do pytest
===================================================
Projeto : Triagem de Chamados de TIC (AGETIC/UFMS)

Carregado automaticamente pelo pytest antes de qualquer test_*.py.
Garante que o sys.path aponte para a raiz do projeto e define fixtures
reutilizáveis para os testes de nós e arestas.

Estrutura esperada:
  projeto/
  ├── nodes/
  ├── utilities/
  ├── state/
  ├── prompts/
  └── tests/
      ├── conftest.py       ← este arquivo
      ├── test_nodes.py
      └── test_edges.py
"""

import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Garante que a raiz do projeto esteja no sys.path
# ─────────────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent if _HERE.name == "tests" else _HERE

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ─────────────────────────────────────────────────────────────────────────────
# Variáveis de ambiente para testes (evita dependência de .env real)
# ─────────────────────────────────────────────────────────────────────────────
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-mocked")
os.environ.setdefault("MODEL_NAME", "test-model")

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures compartilhadas
# ─────────────────────────────────────────────────────────────────────────────
import pytest


@pytest.fixture
def valid_ticket():
    """Ticket válido e completo para uso geral nos testes."""
    return {
        "id": "TKT-TEST-001",
        "timestamp": "2025-05-14T10:00:00",
        "channel": "sistema de chamados",
        "requester_profile": "professor",
        "free_text": "Meu computador não está ligando desde ontem.",
        "needs_more_info": False,
        "info_justification": "",
    }


@pytest.fixture
def valid_response():
    """Objeto Response parcialmente preenchido para uso geral nos testes."""
    return {
        "ticket_id": "TKT-TEST-001",
        "category": "Incidente",
        "category_justification": "Falha em equipamento",
        "urgency": 3,
        "impact": 3,
        "resulting_priority": 3,
        "priority_justification": "Prioridade média",
        "service_type": "Suporte de Campo",
        "support_level": 2,
        "department": "N2 - Suporte de Campo",
        "response_draft": "",
        "validation_status": True,
    }


@pytest.fixture
def base_state(valid_ticket, valid_response):
    """Estado completo (State) para uso geral nos testes."""
    return {
        "ticket": valid_ticket,
        "response": valid_response,
        "closing_message": None,
    }