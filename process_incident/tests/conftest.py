import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Garante que a raiz do projeto esteja no sys.path
# ─────────────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent.parent.parent if _HERE.name == "tests" else _HERE.parent

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
def valid_incident():
    """Incidente válido e completo para uso geral nos testes."""
    return {
        "id": "INC-TEST-001",
        "timestamp": "2026-03-10T07:42:00Z",
        "free_text": (
            "Recebi um e-mail suspeito pedindo para confirmar meus dados "
            "do Passaporte UFMS em um link externo. O link parece falso. "
            "Não cliquei, mas vários colegas do meu laboratório receberam "
            "a mesma mensagem."
        ),
        "validation_status": True,
        "category": "Phishing",
        "category_justification": "Tentativa de phishing via e-mail institucional.",
        "critical": False,
        "critical_justification": "Escopo limitado, nenhum dado comprometido.",
        "scope": "Laboratório de Informática",
        "affected_systems": "Institutional Email",
        "responsible_person": "João Silva",
        "contact_info": "joao.silva@agetic.ufms.br | (67) 3345-7200",
        "containment_steps": [
            "Não clicar em links suspeitos.",
            "Reportar o e-mail ao ETIR.",
            "Verificar logs do servidor de e-mail.",
        ],
        "containment_justification": "Passos padrão para contenção de phishing.",
        "alert_draft": "Prezado João Silva, detectamos um incidente de phishing...",
        "report_template": "# Relatório Parcial de Incidente\n...",
    }


@pytest.fixture
def valid_incident_critical():
    """Incidente crítico para testes de criticidade alta."""
    return {
        "id": "INC-TEST-002",
        "timestamp": "2026-03-11T03:00:00Z",
        "free_text": (
            "O servidor de autenticação LDAP está fora do ar desde as 03h. "
            "Nenhum usuário consegue fazer login nos sistemas institucionais. "
            "Todos os laboratórios e serviços estão impactados."
        ),
        "validation_status": True,
        "category": "Indisponibilidade Crítica",
        "category_justification": "Sistema crítico indisponível afetando toda a instituição.",
        "critical": True,
        "critical_justification": "Afeta sistemas críticos de autenticação institucionais.",
        "scope": "Institucional",
        "affected_systems": "LDAP Authentication Server",
        "responsible_person": "Maria Souza",
        "contact_info": "maria.souza@agetic.ufms.br | (67) 3345-7201",
        "containment_steps": [
            "Isolar o servidor afetado imediatamente.",
            "Acionar backup de autenticação.",
            "Notificar todos os gestores de sistema.",
        ],
        "containment_justification": "Incidente crítico requer ação imediata.",
        "alert_draft": "[CRÍTICO] Incidente de indisponibilidade — ação imediata necessária.",
        "report_template": "# Relatório Parcial de Incidente CRÍTICO\n...",
    }


@pytest.fixture
def base_state(valid_incident):
    """Estado completo (IncidentState) para uso geral nos testes."""
    return {
        "incident": valid_incident,
    }


@pytest.fixture
def base_state_critical(valid_incident_critical):
    """Estado com incidente crítico para testes de alta severidade."""
    return {
        "incident": valid_incident_critical,
    }


@pytest.fixture
def sample_inventory():
    """Inventário sintético de sistemas e responsáveis para testes de lookup."""
    return [
        {
            "system": "Institutional Email",
            "aliases": ["email institucional", "webmail", "zimbra"],
            "responsible_person": "João Silva",
            "contact_info": "joao.silva@agetic.ufms.br | (67) 3345-7200",
        },
        {
            "system": "LDAP Authentication Server",
            "aliases": ["ldap", "active directory", "autenticação"],
            "responsible_person": "Maria Souza",
            "contact_info": "maria.souza@agetic.ufms.br | (67) 3345-7201",
        },
        {
            "system": "Desconhecido",
            "aliases": [],
            "responsible_person": "ETIR - Equipe de Tratamento e Resposta a Incidentes",
            "contact_info": "etir@agetic.ufms.br | (67) 3345-7200",
        },
    ]