"""
test_nodes.py — Testes Unitários dos Nós do Grafo LangGraph
============================================================
Projeto : Triagem de Chamados de TIC (AGETIC/UFMS)

Estratégia
----------
• Cada nó é testado como função pura, chamando-o diretamente com um
  dicionário de estado mockado.
• Nenhuma chamada real a LLMs ou APIs externas é feita. Todos os
  pontos de integração externa são substituídos por MagicMock /
  patch do unittest.mock.
• Os asserts incidem sobre o dicionário de *update* retornado pelo nó
  (o que ele devolve), não sobre o estado completo pós-merge do
  LangGraph.

Nós cobertos
------------
  1. ingest           — Validação Pydantic do ticket bruto
  2. validate_input   — Consulta ao LLM para verificar completude
  3. classify_type    — Classificação de categoria/tipo via LLM
  4. score_priority   — Cálculo paralelo de urgência, impacto e prioridade
  5. draft_response   — Geração de rascunho de resposta via LLM
  6. draft_request    — Geração de rascunho de solicitação de info
  7. queue_only       — Enfileiramento para analista humano (I/O de arquivo)
  8. emit             — Persistência em JSON e CSV
"""

import json
import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES LOCAIS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def valid_ticket():
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
    return {
        "ticket": valid_ticket,
        "response": valid_response,
        "closing_message": None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. NÓ: ingest
# ═══════════════════════════════════════════════════════════════════════════════

class TestIngestNode:
    """Testa o nó `ingest` que valida e normaliza o ticket de entrada."""

    def test_ingest_ticket_valido_retorna_ticket_normalizado(self, valid_ticket):
        """Com um ticket válido, deve retornar o ticket normalizado e
        validation_status=True."""
        from core.nodes.ingest import ingest

        state = {
            "ticket": valid_ticket,
            "response": {},
            "closing_message": None,
        }
        result = ingest(state)

        assert "ticket" in result
        assert result["ticket"]["id"] == "TKT-TEST-001"
        # O free_text deve ter sido normalizado (lowercase, strip, collapse)
        assert result["ticket"]["free_text"] == "meu computador não está ligando desde ontem."

    def test_ingest_valida_status_True_quando_valido(self, valid_ticket):
        """validation_status deve ser True quando o ticket é válido."""
        from core.nodes.ingest import ingest

        state = {"ticket": valid_ticket, "response": {}, "closing_message": None}
        result = ingest(state)

        assert result["response"]["validation_status"] is True

    def test_ingest_normaliza_free_text(self):
        """O free_text com espaços e maiúsculas deve ser normalizado."""
        from core.nodes.ingest import ingest

        ticket = {
            "id": "TKT-NORM-001",
            "timestamp": "2025-05-14T10:00:00",
            "channel": "email",
            "requester_profile": "estudante",
            "free_text": "  TEXTO   Com   Espaços   EXTRAS  ",
            "needs_more_info": False,
            "info_justification": "",
        }
        state = {"ticket": ticket, "response": {}, "closing_message": None}
        result = ingest(state)

        assert result["ticket"]["free_text"] == "texto com espaços extras"

    def test_ingest_ticket_invalido_sem_id(self):
        """Ticket sem campo obrigatório 'id' deve resultar em
        validation_status=False e não retornar 'ticket' no update."""
        from core.nodes.ingest import ingest

        ticket_invalido = {
            # 'id' ausente propositalmente
            "timestamp": "2025-05-14T10:00:00",
            "channel": "email",
            "requester_profile": "estudante",
            "free_text": "Problema com acesso ao sistema.",
            "needs_more_info": False,
            "info_justification": "",
        }
        state = {"ticket": ticket_invalido, "response": {}, "closing_message": None}
        result = ingest(state)

        assert result["response"]["validation_status"] is False
        assert "ticket" not in result  # nó não retorna ticket em caso de falha

    def test_ingest_ticket_invalido_free_text_curto(self):
        """free_text com menos de 2 caracteres deve falhar validação."""
        from core.nodes.ingest import ingest

        ticket_invalido = {
            "id": "TKT-BAD-001",
            "timestamp": "2025-05-14T10:00:00",
            "channel": "email",
            "requester_profile": "estudante",
            "free_text": "x",  # min_length=2
            "needs_more_info": False,
            "info_justification": "",
        }
        state = {"ticket": ticket_invalido, "response": {}, "closing_message": None}
        result = ingest(state)

        assert result["response"]["validation_status"] is False

    def test_ingest_ticket_invalido_channel_vazio(self):
        """Channel vazio deve falhar a validação Pydantic."""
        from core.nodes.ingest import ingest

        ticket_invalido = {
            "id": "TKT-BAD-002",
            "timestamp": "2025-05-14T10:00:00",
            "channel": "",   # min_length=1
            "requester_profile": "estudante",
            "free_text": "Problema de rede.",
            "needs_more_info": False,
            "info_justification": "",
        }
        state = {"ticket": ticket_invalido, "response": {}, "closing_message": None}
        result = ingest(state)

        assert result["response"]["validation_status"] is False

    def test_ingest_preserva_estado_parcial_de_response(self, valid_ticket):
        """Campos já existentes em 'response' não devem ser apagados pelo ingest."""
        from core.nodes.ingest import ingest

        state = {
            "ticket": valid_ticket,
            "response": {"algum_campo_existente": "valor_existente"},
            "closing_message": None,
        }
        result = ingest(state)

        assert result["response"]["algum_campo_existente"] == "valor_existente"

    def test_ingest_ticket_invalido_response_draft_contem_json_do_erro(self):
        """Em caso de ValidationError, response_draft deve conter o JSON do erro."""
        from core.nodes.ingest import ingest

        ticket_invalido = {
            "id": "TKT-ERR-001",
            "timestamp": "2025-05-14T10:00:00",
            "channel": "",
            "requester_profile": "estudante",
            "free_text": "Problema.",
            "needs_more_info": False,
            "info_justification": "",
        }
        state = {"ticket": ticket_invalido, "response": {}, "closing_message": None}
        result = ingest(state)

        # response_draft deve ser uma string com JSON de erro
        assert isinstance(result["response"]["response_draft"], str)
        # e deve ser parseável como JSON
        errors = json.loads(result["response"]["response_draft"])
        assert isinstance(errors, list)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. NÓ: validate_input
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateInputNode:
    """Testa o nó `validate_input` que consulta o LLM para checar completude."""

    @patch("core.nodes.validate_input.load_prompt", return_value="system_prompt_mock")
    @patch("core.nodes.validate_input.call_llm")
    def test_validate_input_completo_needs_more_info_false(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """LLM indica que o ticket está completo → needs_more_info=False."""
        from core.nodes.validate_input import validate_input

        mock_call_llm.return_value = {
            "needs_more_info": False,
            "info_justification": "O ticket contém informações suficientes.",
        }

        result = validate_input(base_state)

        assert "ticket" in result
        assert result["ticket"]["needs_more_info"] is False
        assert result["ticket"]["info_justification"] == "O ticket contém informações suficientes."

    @patch("core.nodes.validate_input.load_prompt", return_value="system_prompt_mock")
    @patch("core.nodes.validate_input.call_llm")
    def test_validate_input_incompleto_needs_more_info_true(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """LLM indica que o ticket está incompleto → needs_more_info=True."""
        from core.nodes.validate_input import validate_input

        mock_call_llm.return_value = {
            "needs_more_info": True,
            "info_justification": "Falta o número do patrimônio do equipamento.",
        }

        result = validate_input(base_state)

        assert result["ticket"]["needs_more_info"] is True
        assert "patrimônio" in result["ticket"]["info_justification"]

    @patch("core.nodes.validate_input.load_prompt", return_value="system_prompt_mock")
    @patch("core.nodes.validate_input.call_llm")
    def test_validate_input_llm_retorna_vazio_usa_defaults(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} o nó deve usar os valores default."""
        from core.nodes.validate_input import validate_input

        mock_call_llm.return_value = {}

        result = validate_input(base_state)

        assert result["ticket"]["needs_more_info"] is False
        assert result["ticket"]["info_justification"] == ""

    @patch("core.nodes.validate_input.load_prompt", return_value="system_prompt_mock")
    @patch("core.nodes.validate_input.call_llm")
    def test_validate_input_preserva_outros_campos_do_ticket(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos pré-existentes no ticket não devem ser removidos."""
        from core.nodes.validate_input import validate_input

        mock_call_llm.return_value = {"needs_more_info": False, "info_justification": "OK"}

        result = validate_input(base_state)

        assert result["ticket"]["id"] == "TKT-TEST-001"
        assert result["ticket"]["channel"] == "sistema de chamados"

    @patch("core.nodes.validate_input.load_prompt", return_value="prompt")
    @patch("core.nodes.validate_input.call_llm")
    def test_validate_input_chama_llm_com_free_text(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O nó deve passar o free_text do ticket para o call_llm."""
        from core.nodes.validate_input import validate_input

        mock_call_llm.return_value = {"needs_more_info": False, "info_justification": ""}

        validate_input(base_state)

        called_user_prompt = mock_call_llm.call_args[0][1]
        assert "Meu computador não está ligando" in called_user_prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NÓ: classify_type
# ═══════════════════════════════════════════════════════════════════════════════

class TestClassifyTypeNode:
    """Testa o nó `classify_type` que classifica categoria, serviço e nível."""

    @patch("core.nodes.classify_type.load_prompt", return_value="system_prompt_mock")
    @patch("core.nodes.classify_type.call_llm")
    def test_classify_type_retorna_campos_corretos(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O update deve conter category, service_type, support_level, etc."""
        from core.nodes.classify_type import classify_type

        mock_call_llm.return_value = {
            "category": "Incidente",
            "service_type": "Suporte de Campo",
            "support_level": 2,
            "category_justification": "Falha em equipamento físico.",
            "department": "N2 - Suporte de Campo",
        }

        result = classify_type(base_state)

        assert "response" in result
        assert result["response"]["category"] == "Incidente"
        assert result["response"]["service_type"] == "Suporte de Campo"
        assert result["response"]["support_level"] == 2
        assert result["response"]["department"] == "N2 - Suporte de Campo"
        assert result["response"]["ticket_id"] == "TKT-TEST-001"

    @patch("core.nodes.classify_type.load_prompt", return_value="prompt")
    @patch("core.nodes.classify_type.call_llm")
    def test_classify_type_llm_retorna_vazio_usa_defaults(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} devem ser usados os valores default."""
        from core.nodes.classify_type import classify_type

        mock_call_llm.return_value = {}

        result = classify_type(base_state)

        assert result["response"]["category"] == "Indefinida"
        assert result["response"]["service_type"] == "Geral"
        assert result["response"]["support_level"] == 1
        assert result["response"]["department"] == "Geral"
        assert result["response"]["category_justification"] == "Sem justificativa"

    @patch("core.nodes.classify_type.load_prompt", return_value="prompt")
    @patch("core.nodes.classify_type.call_llm")
    def test_classify_type_preserva_campos_existentes_em_response(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos já presentes em response (ex: urgency) não devem ser apagados."""
        from core.nodes.classify_type import classify_type

        mock_call_llm.return_value = {
            "category": "Requisição",
            "service_type": "Geral",
            "support_level": 1,
            "category_justification": "Pedido de instalação.",
            "department": "N1 - Atendimento",
        }

        result = classify_type(base_state)

        # urgency e impact do base_state devem sobreviver no dict retornado
        assert result["response"]["urgency"] == 3
        assert result["response"]["impact"] == 3

    @patch("core.nodes.classify_type.load_prompt", return_value="prompt")
    @patch("core.nodes.classify_type.call_llm")
    def test_classify_type_chama_load_prompt_e_call_llm(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Os helpers load_prompt e call_llm devem ser chamados exatamente 1 vez."""
        from core.nodes.classify_type import classify_type

        mock_call_llm.return_value = {
            "category": "Incidente",
            "service_type": "Suporte",
            "support_level": 1,
            "category_justification": "Falha.",
            "department": "N1",
        }

        classify_type(base_state)

        mock_load_prompt.assert_called_once()
        mock_call_llm.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. NÓ: score_priority   (internos: _calculate_priority)
# ═══════════════════════════════════════════════════════════════════════════════

class TestScorePriorityNode:
    """Testa o nó `score_priority` incluindo a função auxiliar _calculate_priority."""

    # ── Testes da função pura _calculate_priority ────────────────────────────

    def test_calculate_priority_valores_iguais(self):
        """urgency==impact==3 deve resultar em prioridade 3."""
        from core.nodes.score_priority import _calculate_priority
        assert _calculate_priority(3, 3) == 3

    def test_calculate_priority_maximo(self):
        """urgency=5, impact=5 → prioridade máxima (5)."""
        from core.nodes.score_priority import _calculate_priority
        assert _calculate_priority(5, 5) == 5

    def test_calculate_priority_minimo(self):
        """urgency=1, impact=1 → prioridade mínima (1)."""
        from core.nodes.score_priority import _calculate_priority
        assert _calculate_priority(1, 1) == 1

    def test_calculate_priority_assimetrico(self):
        """urgency=5, impact=1 → prioridade deve ser dominada pelo max=5."""
        from core.nodes.score_priority import _calculate_priority
        result = _calculate_priority(5, 1)
        assert 1 <= result <= 5

    def test_calculate_priority_clamp_superior(self):
        """A função nunca retorna valor acima de PRIORITY_MAX (5)."""
        from core.nodes.score_priority import _calculate_priority
        result = _calculate_priority(5, 5)
        assert result <= 5

    def test_calculate_priority_clamp_inferior(self):
        """A função nunca retorna valor abaixo de PRIORITY_MIN (1)."""
        from core.nodes.score_priority import _calculate_priority
        result = _calculate_priority(1, 1)
        assert result >= 1

    # ── Testes do nó score_priority com LLM mockado ──────────────────────────

    @patch("core.nodes.score_priority.load_prompt", return_value="prompt")
    @patch("core.nodes.score_priority.call_llm")
    def test_score_priority_caminho_feliz(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Fluxo normal: urgência e impacto retornados, prioridade calculada."""
        from core.nodes.score_priority import score_priority

        # call_llm é chamado 3x: urgência, impacto, justificativa
        mock_call_llm.side_effect = [
            {"urgency": 4},
            {"impact": 3},
            {"priority_justification": "Alta urgência detectada."},
        ]

        result = score_priority(base_state)

        assert "response" in result
        assert result["response"]["urgency"] == 4
        assert result["response"]["impact"] == 3
        assert 1 <= result["response"]["resulting_priority"] <= 5
        assert result["response"]["priority_justification"] == "Alta urgência detectada."

    @patch("core.nodes.score_priority.load_prompt", return_value="prompt")
    @patch("core.nodes.score_priority.call_llm")
    def test_score_priority_failsafe_quando_urgency_falha(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Falha no LLM de urgência → prioridade escalada ao máximo (5)."""
        from core.nodes.score_priority import score_priority, FAILSAFE_PRIORITY, DEFAULT_SCORE

        mock_call_llm.side_effect = [
            {},            # urgência falha
            {"impact": 3}, # impacto ok
        ]

        result = score_priority(base_state)

        assert result["response"]["resulting_priority"] == FAILSAFE_PRIORITY
        assert result["response"]["urgency"] == DEFAULT_SCORE
        assert "llm_error" in result["response"]

    @patch("core.nodes.score_priority.load_prompt", return_value="prompt")
    @patch("core.nodes.score_priority.call_llm")
    def test_score_priority_failsafe_quando_impact_falha(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Falha no LLM de impacto → prioridade escalada ao máximo (5)."""
        from core.nodes.score_priority import score_priority, FAILSAFE_PRIORITY

        mock_call_llm.side_effect = [
            {"urgency": 3},
            {},             # impacto falha
        ]

        result = score_priority(base_state)

        assert result["response"]["resulting_priority"] == FAILSAFE_PRIORITY
        assert "llm_error" in result["response"]

    @patch("core.nodes.score_priority.load_prompt", return_value="prompt")
    @patch("core.nodes.score_priority.call_llm")
    def test_score_priority_justificativa_fallback(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM de justificativa retorna {} usa texto de fallback."""
        from core.nodes.score_priority import score_priority

        mock_call_llm.side_effect = [
            {"urgency": 2},
            {"impact": 2},
            {},   # justificativa falha — deve usar fallback
        ]

        result = score_priority(base_state)

        justification = result["response"]["priority_justification"]
        assert isinstance(justification, str) and len(justification) > 0

    @patch("core.nodes.score_priority.load_prompt", return_value="prompt")
    @patch("core.nodes.score_priority.call_llm")
    def test_score_priority_preserva_campos_anteriores(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos pré-existentes em response (category, etc.) devem persistir."""
        from core.nodes.score_priority import score_priority

        mock_call_llm.side_effect = [
            {"urgency": 3},
            {"impact": 3},
            {"priority_justification": "Justificativa OK."},
        ]

        result = score_priority(base_state)

        assert result["response"]["category"] == "Incidente"
        assert result["response"]["department"] == "N2 - Suporte de Campo"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. NÓ: draft_response
# ═══════════════════════════════════════════════════════════════════════════════

class TestDraftResponseNode:
    """Testa o nó `draft_response` que gera o rascunho de resposta ao usuário."""

    @patch("core.nodes.draft_response.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_response.build_few_shot", return_value="few_shot_examples")
    @patch("core.nodes.draft_response.call_llm")
    def test_draft_response_retorna_response_draft(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, base_state
    ):
        """O nó deve retornar a chave 'response' com 'response_draft' preenchido."""
        from core.nodes.draft_response import draft_response

        mock_call_llm.return_value = {
            "response_draft": "Olá professor, seu chamado foi registrado."
        }

        result = draft_response(base_state)

        assert "response" in result
        assert result["response"]["response_draft"] == "Olá professor, seu chamado foi registrado."

    @patch("core.nodes.draft_response.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_response.build_few_shot", return_value="")
    @patch("core.nodes.draft_response.call_llm")
    def test_draft_response_llm_vazio_retorna_string_vazia(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} o response_draft deve ser string vazia."""
        from core.nodes.draft_response import draft_response

        mock_call_llm.return_value = {}

        result = draft_response(base_state)

        assert result["response"]["response_draft"] == ""

    @patch("core.nodes.draft_response.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_response.build_few_shot", return_value="exemplos")
    @patch("core.nodes.draft_response.call_llm")
    def test_draft_response_chama_build_few_shot_com_department(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, base_state
    ):
        """O nó deve usar o department do state para construir few-shot."""
        from core.nodes.draft_response import draft_response

        mock_call_llm.return_value = {"response_draft": "Resposta."}

        draft_response(base_state)

        mock_few_shot.assert_called_once_with("N2 - Suporte de Campo")

    @patch("core.nodes.draft_response.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_response.build_few_shot", return_value="exemplos")
    @patch("core.nodes.draft_response.call_llm")
    def test_draft_response_preserva_campos_existentes_em_response(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, base_state
    ):
        """Campos pré-existentes como urgency/impact devem sobreviver."""
        from core.nodes.draft_response import draft_response

        mock_call_llm.return_value = {"response_draft": "Rascunho gerado."}

        result = draft_response(base_state)

        assert result["response"]["urgency"] == 3
        assert result["response"]["category"] == "Incidente"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. NÓ: draft_request
# ═══════════════════════════════════════════════════════════════════════════════

class TestDraftRequestNode:
    """Testa o nó `draft_request` que gera solicitação de mais informações."""

    @patch("core.nodes.draft_request.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_request.call_llm")
    def test_draft_request_retorna_response_draft(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O nó deve retornar 'response' com 'response_draft' preenchido."""
        from core.nodes.draft_request import draft_request

        mock_call_llm.return_value = {
            "response_draft": "Por favor, informe o número de patrimônio do equipamento."
        }

        result = draft_request(base_state)

        assert "response" in result
        assert "patrimônio" in result["response"]["response_draft"]

    @patch("core.nodes.draft_request.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_request.call_llm")
    def test_draft_request_llm_vazio_retorna_string_vazia(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} o response_draft deve ser string vazia."""
        from core.nodes.draft_request import draft_request

        mock_call_llm.return_value = {}

        result = draft_request(base_state)

        assert result["response"]["response_draft"] == ""

    @patch("core.nodes.draft_request.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_request.call_llm")
    def test_draft_request_passa_free_text_ao_llm(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O free_text do ticket deve estar presente no user_prompt enviado ao LLM."""
        from core.nodes.draft_request import draft_request

        mock_call_llm.return_value = {"response_draft": "Solicito mais informações."}

        draft_request(base_state)

        user_prompt = mock_call_llm.call_args[0][1]
        assert "Meu computador não está ligando" in user_prompt

    @patch("core.nodes.draft_request.load_prompt", return_value="prompt")
    @patch("core.nodes.draft_request.call_llm")
    def test_draft_request_preserva_campos_de_response(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos existentes em response não devem ser removidos."""
        from core.nodes.draft_request import draft_request

        mock_call_llm.return_value = {"response_draft": "Preciso de mais dados."}

        result = draft_request(base_state)

        assert result["response"]["category"] == "Incidente"
        assert result["response"]["urgency"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 7. NÓ: queue_only
# ═══════════════════════════════════════════════════════════════════════════════

class TestQueueOnlyNode:
    """Testa o nó `queue_only` que encaminha o ticket para fila humana."""

    @patch("core.nodes.queue_only.open", new_callable=mock_open, read_data="[]")
    @patch("core.nodes.queue_only.json.dump")
    @patch("core.nodes.queue_only.json.load", return_value=[])
    def test_queue_only_retorna_response_draft_fila(
        self, mock_json_load, mock_json_dump, mock_file, base_state
    ):
        """O nó deve definir response_draft como a mensagem de fila humana."""
        from core.nodes.queue_only import queue_only

        result = queue_only(base_state)

        assert "response" in result
        assert "[FILA HUMANA]" in result["response"]["response_draft"]

    @patch("core.nodes.queue_only.open", new_callable=mock_open, read_data="[]")
    @patch("core.nodes.queue_only.json.dump")
    @patch("core.nodes.queue_only.json.load", return_value=[])
    def test_queue_only_preserva_campos_existentes(
        self, mock_json_load, mock_json_dump, mock_file, base_state
    ):
        """Campos pré-existentes em response devem ser preservados."""
        from core.nodes.queue_only import queue_only

        result = queue_only(base_state)

        assert result["response"]["category"] == "Incidente"
        assert result["response"]["urgency"] == 3

    @patch("core.nodes.queue_only.open", new_callable=mock_open)
    @patch("core.nodes.queue_only.json.dump")
    def test_queue_only_cria_fila_quando_arquivo_nao_existe(
        self, mock_json_dump, mock_file, base_state
    ):
        """Quando o arquivo da fila não existe, começa com lista vazia."""
        from core.nodes.queue_only import queue_only

        # Simula FileNotFoundError na leitura
        mock_file.side_effect = [FileNotFoundError, mock_open()()]

        with patch("core.nodes.queue_only.json.load", side_effect=FileNotFoundError):
            # Re-patch open sem side_effect
            with patch("core.nodes.queue_only.open", mock_open()) as mocked:
                with patch("core.nodes.queue_only.json.dump") as mocked_dump:
                    result = queue_only(base_state)

        assert "[FILA HUMANA]" in result["response"]["response_draft"]

    @patch("core.nodes.queue_only.open", new_callable=mock_open, read_data="[]")
    @patch("core.nodes.queue_only.json.load", return_value=[{"ticket_id": "ANTIGO"}])
    @patch("core.nodes.queue_only.json.dump")
    def test_queue_only_adiciona_entrada_a_fila_existente(
        self, mock_json_dump, mock_json_load, mock_file, base_state
    ):
        """O ticket novo deve ser adicionado à fila existente (append)."""
        from core.nodes.queue_only import queue_only

        queue_only(base_state)

        # json.dump deve ter sido chamado com lista de 2 itens
        dumped_queue = mock_json_dump.call_args[0][0]
        assert len(dumped_queue) == 2
        assert dumped_queue[0]["ticket_id"] == "ANTIGO"
        assert dumped_queue[1]["ticket_id"] == "TKT-TEST-001"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. NÓ: emit
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmitNode:
    """Testa o nó `emit` que persiste o resultado em JSON e CSV."""

    def _make_emit_state(self, valid_ticket, valid_response):
        """Estado mínimo necessário para o nó emit funcionar."""
        response = dict(valid_response)
        response["response_draft"] = "Olá, seu chamado foi registrado."
        return {
            "ticket": valid_ticket,
            "response": response,
            "closing_message": None,
        }

    @patch("core.nodes.emit.open", new_callable=mock_open)
    @patch("core.nodes.emit.os.makedirs")
    @patch("core.nodes.emit.REPORT_CSV")
    @patch("core.nodes.emit.RESPONSES_PATH")
    def test_emit_retorna_closing_message(
        self, mock_dir, mock_csv, mock_makedirs, mock_file,
        valid_ticket, valid_response
    ):
        """O nó deve retornar closing_message com texto padrão de encerramento."""
        from core.nodes.emit import emit

        mock_dir.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_ticket, valid_response)

        with patch("core.nodes.emit.csv.DictWriter") as mock_writer_cls:
            mock_writer = MagicMock()
            mock_writer_cls.return_value = mock_writer
            result = emit(state)

        assert "closing_message" in result
        assert "AGETIC/UFMS" in result["closing_message"]
        assert "suporte.agetic@ufms.br" in result["closing_message"]

    @patch("core.nodes.emit.open", new_callable=mock_open)
    @patch("core.nodes.emit.os.makedirs")
    @patch("core.nodes.emit.REPORT_CSV")
    @patch("core.nodes.emit.RESPONSES_PATH")
    def test_emit_retorna_response_com_ticket_id(
        self, mock_dir, mock_csv, mock_makedirs, mock_file,
        valid_ticket, valid_response
    ):
        """O response retornado deve conter o ticket_id correto."""
        from core.nodes.emit import emit

        mock_dir.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_ticket, valid_response)

        with patch("core.nodes.emit.csv.DictWriter") as mock_writer_cls:
            mock_writer = MagicMock()
            mock_writer_cls.return_value = mock_writer
            result = emit(state)

        assert result["response"]["ticket_id"] == "TKT-TEST-001"

    @patch("core.nodes.emit.open", new_callable=mock_open)
    @patch("core.nodes.emit.os.makedirs")
    @patch("core.nodes.emit.REPORT_CSV")
    @patch("core.nodes.emit.RESPONSES_PATH")
    def test_emit_retorna_campos_obrigatorios(
        self, mock_dir, mock_csv, mock_makedirs, mock_file,
        valid_ticket, valid_response
    ):
        """O response deve conter todos os campos esperados no output."""
        from core.nodes.emit import emit

        mock_dir.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_ticket, valid_response)

        with patch("core.nodes.emit.csv.DictWriter") as mock_writer_cls:
            mock_writer = MagicMock()
            mock_writer_cls.return_value = mock_writer
            result = emit(state)

        expected_keys = {
            "ticket_id", "category", "urgency", "impact",
            "resulting_priority", "priority_justification",
            "service_type", "support_level", "department",
            "response_draft", "needs_more_info", "info_justification",
        }
        for key in expected_keys:
            assert key in result["response"], f"Chave '{key}' ausente no response"

    @patch("core.nodes.emit.open", new_callable=mock_open)
    @patch("core.nodes.emit.os.makedirs")
    @patch("core.nodes.emit.REPORT_CSV")
    @patch("core.nodes.emit.RESPONSES_PATH")
    def test_emit_chama_makedirs(
        self, mock_dir, mock_csv, mock_makedirs, mock_file,
        valid_ticket, valid_response
    ):
        """O nó deve garantir que o diretório de respostas exista."""
        from core.nodes.emit import emit

        mock_dir.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_ticket, valid_response)

        with patch("core.nodes.emit.csv.DictWriter") as mock_writer_cls:
            mock_writer = MagicMock()
            mock_writer_cls.return_value = mock_writer
            emit(state)

        mock_makedirs.assert_called_once()