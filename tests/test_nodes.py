"""
Suíte de Testes Unitários — Nós do Grafo LangGraph
=====================================================
Projeto : Triagem de Chamados de TIC (AGETIC/UFMS)
Arquivo : test_nodes.py
Cobertura: ingest | classify_type | score_priority | draft_response
            emit  | queue_only

Execução:
    pytest tests/test_nodes.py -v

Pré-requisitos (instale no venv do projeto):
    pip install pytest pytest-asyncio pydantic
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES GLOBAIS — dados reutilizados em toda a suíte
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def valid_ticket() -> dict:
    """Ticket válido e completo, representando um State inicial correto."""
    return {
        "id": "TKT-001",
        "timestamp": "2025-05-14T10:00:00",
        "channel": "sistema",
        "requester_profile": "professor",
        "free_text": "O meu notebook não liga desde ontem.",
    }


@pytest.fixture
def base_response() -> dict:
    """Dicionário `response` parcial já populado pelos nós anteriores."""
    return {
        "ticket_id": "TKT-001",
        "category": "Incidente",
        "category_justification": "Falha em hardware.",
        "urgency": 3,
        "impact": 4,
        "resulting_priority": 4,
        "priority_justification": "Impacto alto.",
        "service_type": "Suporte de Campo",
        "support_level": 2,
        "department": "N2 - Suporte de Campo",
        "response_draft": "",
        "validation_status": True,
    }


@pytest.fixture
def state_valid(valid_ticket, base_response) -> dict:
    """Estado completo e válido para testes que exigem múltiplos campos."""
    return {
        "ticket": valid_ticket,
        "response": base_response,
        "closing_message": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1.  NÓ: ingest
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestNode:
    """Testa o nó `ingest` em completo isolamento."""

    def test_ingest_ticket_valido_retorna_ticket_normalizado(self, valid_ticket):
        """Ticket válido → retorna chave 'ticket' com texto normalizado."""
        from nodes.ingest import ingest

        state = {"ticket": valid_ticket, "response": {}}
        result = ingest(state)

        assert "ticket" in result, "O update deve conter a chave 'ticket'."
        assert result["ticket"]["id"] == "TKT-001"
        # O validator normalize_text converte para minúsculas e remove espaços extras
        assert result["ticket"]["free_text"] == "o meu notebook não liga desde ontem."

    def test_ingest_ticket_valido_validation_status_true(self, valid_ticket):
        """Ticket válido → validation_status deve ser True."""
        from nodes.ingest import ingest

        state = {"ticket": valid_ticket, "response": {}}
        result = ingest(state)

        assert result["response"]["validation_status"] is True

    def test_ingest_ticket_invalido_retorna_validation_false(self):
        """Ticket sem 'free_text' válido → validation_status deve ser False."""
        from nodes.ingest import ingest

        invalid_ticket = {
            "id": "TKT-ERR",
            "timestamp": "2025-05-14T10:00:00",
            "channel": "email",
            "requester_profile": "estudante",
            "free_text": "",          # falha na validação (min_length=2)
        }
        state = {"ticket": invalid_ticket, "response": {}}
        result = ingest(state)

        assert result["response"]["validation_status"] is False
        # Não deve retornar a chave 'ticket' quando a validação falha
        assert "ticket" not in result

    def test_ingest_ticket_invalido_contem_error_json(self):
        """Quando a validação falha, response_draft deve conter o JSON de erro do Pydantic."""
        from nodes.ingest import ingest

        invalid_ticket = {
            "id": "",                 # id vazio: viola Field obrigatório
            "timestamp": "invalido",  # timestamp não é datetime
            "channel": "telefone",
            "requester_profile": "técnico",
            "free_text": "Problema",
        }
        state = {"ticket": invalid_ticket, "response": {}}
        result = ingest(state)

        assert result["response"]["validation_status"] is False
        # response_draft deve ser uma string de erro serializável
        assert isinstance(result["response"]["response_draft"], str)

    def test_ingest_preserva_response_existente(self, valid_ticket):
        """Ingest não deve apagar campos de 'response' já populados anteriormente."""
        from nodes.ingest import ingest

        state = {
            "ticket": valid_ticket,
            "response": {"ticket_id": "TKT-001", "category": "Incidente"},
        }
        result = ingest(state)

        # Os campos pré-existentes devem ser preservados no merge
        assert result["response"].get("category") == "Incidente"

    def test_ingest_sem_ticket_retorna_validation_false(self):
        """Estado sem a chave 'ticket' deve resultar em validação falsa."""
        from nodes.ingest import ingest

        state = {"ticket": None, "response": {}}
        result = ingest(state)

        assert result["response"]["validation_status"] is False

    def test_ingest_normaliza_espacos_extras(self):
        """free_text com espaços e maiúsculas deve ser normalizado."""
        from nodes.ingest import ingest

        ticket = {
            "id": "TKT-002",
            "timestamp": "2025-05-14T09:00:00",
            "channel": "email",
            "requester_profile": "professor",
            "free_text": "   MEU   COMPUTADOR   NÃO LIGA  ",
        }
        state = {"ticket": ticket, "response": {}}
        result = ingest(state)

        assert result["ticket"]["free_text"] == "meu computador não liga"


# ─────────────────────────────────────────────────────────────────────────────
# 2.  NÓ: classify_type
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyTypeNode:
    """Testa o nó `classify_type`, mockando call_llm e load_prompt."""

    def _make_state(self, valid_ticket, base_response):
        return {
            "ticket": valid_ticket,
            "response": base_response,
            "closing_message": None,
        }

    @patch("nodes.classify_type.load_prompt", return_value="<system prompt>")
    @patch("nodes.classify_type.call_llm")
    def test_classify_retorna_categoria_correta(
        self, mock_call_llm, mock_load_prompt, valid_ticket, base_response
    ):
        """LLM retorna JSON válido → response deve ter category e campos derivados."""
        from nodes.classify_type import classify_type

        mock_call_llm.return_value = {
            "category": "Incidente",
            "service_type": "Suporte de Campo",
            "support_level": 2,
            "category_justification": "Equipamento com defeito.",
            "department": "N2 - Suporte de Campo",
        }

        state = self._make_state(valid_ticket, base_response)
        result = classify_type(state)

        assert "response" in result
        assert result["response"]["category"] == "Incidente"
        assert result["response"]["service_type"] == "Suporte de Campo"
        assert result["response"]["support_level"] == 2
        assert result["response"]["department"] == "N2 - Suporte de Campo"

    @patch("nodes.classify_type.load_prompt", return_value="<system prompt>")
    @patch("nodes.classify_type.call_llm")
    def test_classify_ticket_id_propagado(
        self, mock_call_llm, mock_load_prompt, valid_ticket, base_response
    ):
        """O ticket_id deve ser copiado para response a partir do estado."""
        from nodes.classify_type import classify_type

        mock_call_llm.return_value = {
            "category": "Requisição",
            "service_type": "Geral",
            "support_level": 1,
            "category_justification": "Solicitação simples.",
            "department": "N1 - Service Desk",
        }

        state = self._make_state(valid_ticket, base_response)
        result = classify_type(state)

        assert result["response"]["ticket_id"] == valid_ticket["id"]

    @patch("nodes.classify_type.load_prompt", return_value="<system prompt>")
    @patch("nodes.classify_type.call_llm", return_value={})
    def test_classify_llm_vazio_usa_defaults(
        self, mock_call_llm, mock_load_prompt, valid_ticket, base_response
    ):
        """LLM retorna dict vazio → campos devem receber valores default."""
        from nodes.classify_type import classify_type

        state = self._make_state(valid_ticket, base_response)
        result = classify_type(state)

        assert result["response"]["category"] == "Indefinida"
        assert result["response"]["service_type"] == "Geral"
        assert result["response"]["support_level"] == 1
        assert result["response"]["category_justification"] == "Sem justificativa"
        assert result["response"]["department"] == "Geral"

    @patch("nodes.classify_type.load_prompt", return_value="<prompt>")
    @patch("nodes.classify_type.call_llm")
    def test_classify_chama_llm_com_free_text(
        self, mock_call_llm, mock_load_prompt, valid_ticket, base_response
    ):
        """Garante que o free_text do ticket é enviado para o LLM."""
        from nodes.classify_type import classify_type

        mock_call_llm.return_value = {"category": "Incidente"}
        state = self._make_state(valid_ticket, base_response)
        classify_type(state)

        call_args = mock_call_llm.call_args
        assert valid_ticket["free_text"] in call_args[0][1]


# ─────────────────────────────────────────────────────────────────────────────
# 3.  NÓ: score_priority
# ─────────────────────────────────────────────────────────────────────────────

class TestScorePriorityNode:
    """
    Testa o nó `score_priority`:
        - cálculo determinístico de prioridade (_calculate_priority)
        - fluxo principal com mock do ThreadPoolExecutor
        - cenários de falha do LLM (fail-safe)
    """

    # ── 3a. Testes da função pura _calculate_priority ──────────────────────

    def test_calculate_priority_valores_iguais(self):
        """Com urgência == impacto, resultado deve ser o mesmo valor."""
        from nodes.score_priority import _calculate_priority
        assert _calculate_priority(3, 3) == 3

    def test_calculate_priority_maximos(self):
        """Urgência 5 e Impacto 5 → prioridade máxima 5."""
        from nodes.score_priority import _calculate_priority
        assert _calculate_priority(5, 5) == 5

    def test_calculate_priority_minimos(self):
        """Urgência 1 e Impacto 1 → prioridade mínima 1."""
        from nodes.score_priority import _calculate_priority
        assert _calculate_priority(1, 1) == 1

    def test_calculate_priority_limite_superior(self):
        """Resultado nunca ultrapassa PRIORITY_MAX (5)."""
        from nodes.score_priority import _calculate_priority
        result = _calculate_priority(5, 5)
        assert result <= 5

    def test_calculate_priority_limite_inferior(self):
        """Resultado nunca cai abaixo de PRIORITY_MIN (1)."""
        from nodes.score_priority import _calculate_priority
        result = _calculate_priority(1, 1)
        assert result >= 1

    def test_calculate_priority_assimetrico(self):
        """Com urgência alta e impacto baixo, o max eleva a prioridade."""
        from nodes.score_priority import _calculate_priority
        result = _calculate_priority(5, 1)
        # max=5, média=(5+1)/2=3 → raw=(5+3)/2=4 → 4
        assert result == 4

    # ── 3b. Testes do nó score_priority completo ───────────────────────────

    @patch("nodes.score_priority.load_prompt", return_value="<prompt>")
    @patch("nodes.score_priority.call_llm")
    def test_score_priority_fluxo_normal(
        self, mock_call_llm, mock_load_prompt, valid_ticket, base_response
    ):
        """
        Fluxo feliz: LLM retorna urgência, impacto e justificativa.
        O nó deve atualizar response com todos os 4 campos.
        """
        from nodes.score_priority import score_priority

        # call_llm é chamado 3 vezes: urgência, impacto, justificativa
        mock_call_llm.side_effect = [
            {"urgency": 4},
            {"impact": 5},
            {"priority_justification": "Risco crítico identificado."},
        ]

        state = {
            "ticket": valid_ticket,
            "response": {"ticket_id": "TKT-001", "category": "Incidente"},
            "closing_message": None,
        }
        result = score_priority(state)

        assert "response" in result
        assert result["response"]["urgency"] == 4
        assert result["response"]["impact"] == 5
        assert isinstance(result["response"]["resulting_priority"], int)
        assert 1 <= result["response"]["resulting_priority"] <= 5
        assert result["response"]["priority_justification"] == "Risco crítico identificado."

    @patch("nodes.score_priority.load_prompt", return_value="<prompt>")
    @patch("nodes.score_priority.call_llm", return_value={})
    def test_score_priority_llm_falha_activa_failsafe(
        self, mock_call_llm, mock_load_prompt, valid_ticket
    ):
        """
        Quando o LLM retorna {} (falha), o nó deve aplicar fail-safe:
        prioridade = FAILSAFE_PRIORITY (5) e marcar llm_error.
        """
        from nodes.score_priority import score_priority, FAILSAFE_PRIORITY

        state = {
            "ticket": valid_ticket,
            "response": {},
            "closing_message": None,
        }
        result = score_priority(state)

        assert result["response"]["resulting_priority"] == FAILSAFE_PRIORITY
        assert "llm_error" in result["response"]
        assert "falhou" in result["response"]["llm_error"].lower()

    @patch("nodes.score_priority.load_prompt", return_value="<prompt>")
    @patch("nodes.score_priority.call_llm")
    def test_score_priority_sem_justificativa_usa_fallback(
        self, mock_call_llm, mock_load_prompt, valid_ticket
    ):
        """
        LLM retorna urgência/impacto mas não retorna priority_justification.
        Nó deve usar fallback textual e não quebrar.
        """
        from nodes.score_priority import score_priority

        mock_call_llm.side_effect = [
            {"urgency": 2},
            {"impact": 2},
            {},    # sem priority_justification
        ]

        state = {"ticket": valid_ticket, "response": {}}
        result = score_priority(state)

        assert "priority_justification" in result["response"]
        assert len(result["response"]["priority_justification"]) > 0

    @patch("nodes.score_priority.load_prompt", return_value="<prompt>")
    @patch("nodes.score_priority.call_llm")
    def test_score_priority_preserva_campos_anteriores(
        self, mock_call_llm, mock_load_prompt, valid_ticket
    ):
        """Campos já presentes em 'response' (ex: category) devem ser preservados."""
        from nodes.score_priority import score_priority

        mock_call_llm.side_effect = [
            {"urgency": 3},
            {"impact": 3},
            {"priority_justification": "Prioridade média."},
        ]

        state = {
            "ticket": valid_ticket,
            "response": {"category": "Requisição", "department": "N1"},
        }
        result = score_priority(state)

        assert result["response"]["category"] == "Requisição"
        assert result["response"]["department"] == "N1"


# ─────────────────────────────────────────────────────────────────────────────
# 4.  NÓ: draft_response
# ─────────────────────────────────────────────────────────────────────────────

class TestDraftResponseNode:
    """Testa o nó `draft_response`, mockando call_llm, load_prompt e build_few_shot."""

    @patch("nodes.draft_response.load_prompt", return_value="<draft prompt>")
    @patch("nodes.draft_response.build_few_shot", return_value="Ticket: ex\nResponse: resp")
    @patch("nodes.draft_response.call_llm")
    def test_draft_response_popula_response_draft(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, state_valid
    ):
        """LLM retorna response_draft → deve ser salvo em response."""
        from nodes.draft_response import draft_response

        mock_call_llm.return_value = {
            "response_draft": "Olá Professor, registramos seu chamado."
        }

        result = draft_response(state_valid)

        assert "response" in result
        assert result["response"]["response_draft"] == "Olá Professor, registramos seu chamado."

    @patch("nodes.draft_response.load_prompt", return_value="<draft prompt>")
    @patch("nodes.draft_response.build_few_shot", return_value="")
    @patch("nodes.draft_response.call_llm", return_value={})
    def test_draft_response_llm_vazio_retorna_string_vazia(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, state_valid
    ):
        """LLM retorna {} → response_draft deve ser string vazia (default)."""
        from nodes.draft_response import draft_response

        result = draft_response(state_valid)

        assert result["response"]["response_draft"] == ""

    @patch("nodes.draft_response.load_prompt", return_value="<draft prompt>")
    @patch("nodes.draft_response.build_few_shot", return_value="examples")
    @patch("nodes.draft_response.call_llm")
    def test_draft_response_preserva_campos_anteriores(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, state_valid
    ):
        """O nó não deve apagar campos já existentes em response (category, urgency, etc.)."""
        from nodes.draft_response import draft_response

        mock_call_llm.return_value = {"response_draft": "Resposta gerada."}
        result = draft_response(state_valid)

        assert result["response"]["category"] == state_valid["response"]["category"]
        assert result["response"]["urgency"] == state_valid["response"]["urgency"]

    @patch("nodes.draft_response.load_prompt", return_value="<prompt>")
    @patch("nodes.draft_response.build_few_shot")
    @patch("nodes.draft_response.call_llm")
    def test_draft_response_usa_department_para_few_shot(
        self, mock_call_llm, mock_few_shot, mock_load_prompt, state_valid
    ):
        """O department do estado deve ser passado para build_few_shot."""
        from nodes.draft_response import draft_response

        mock_few_shot.return_value = ""
        mock_call_llm.return_value = {"response_draft": "resp"}

        draft_response(state_valid)

        mock_few_shot.assert_called_once_with(state_valid["response"]["department"])


# ─────────────────────────────────────────────────────────────────────────────
# 5.  NÓ: emit
# ─────────────────────────────────────────────────────────────────────────────

class TestEmitNode:
    """
    Testa o nó `emit`.
    Usa patch em os.makedirs e open para evitar I/O real no disco.
    """

    def test_emit_retorna_closing_message(self, state_valid, tmp_path, monkeypatch):
        """O nó deve sempre retornar closing_message não-vazia."""
        from nodes.emit import emit
        import nodes.emit as emit_module

        monkeypatch.setattr(emit_module, "RESPONSES_DIR", tmp_path)
        monkeypatch.setattr(emit_module, "REPORT_CSV", tmp_path / "report.csv")

        result = emit(state_valid)

        assert "closing_message" in result
        assert len(result["closing_message"]) > 0

    def test_emit_retorna_response_com_ticket_id(self, state_valid, tmp_path, monkeypatch):
        """Response retornada pelo emit deve conter o ticket_id correto."""
        from nodes.emit import emit
        import nodes.emit as emit_module

        monkeypatch.setattr(emit_module, "RESPONSES_DIR", tmp_path)
        monkeypatch.setattr(emit_module, "REPORT_CSV", tmp_path / "report.csv")

        result = emit(state_valid)

        assert result["response"]["ticket_id"] == "TKT-001"

    def test_emit_cria_arquivo_json(self, state_valid, tmp_path, monkeypatch):
        """O nó deve criar um arquivo JSON com o nome correto no RESPONSES_DIR."""
        from nodes.emit import emit
        import nodes.emit as emit_module

        monkeypatch.setattr(emit_module, "RESPONSES_DIR", tmp_path)
        monkeypatch.setattr(emit_module, "REPORT_CSV", tmp_path / "report.csv")

        emit(state_valid)

        expected_file = tmp_path / "ticket_TKT-001.json"
        assert expected_file.exists(), "Arquivo JSON do ticket não foi criado."

    def test_emit_conteudo_json_correto(self, state_valid, tmp_path, monkeypatch):
        """O JSON gerado deve conter os campos principais com os valores do estado."""
        from nodes.emit import emit
        import nodes.emit as emit_module

        monkeypatch.setattr(emit_module, "RESPONSES_DIR", tmp_path)
        monkeypatch.setattr(emit_module, "REPORT_CSV", tmp_path / "report.csv")

        emit(state_valid)

        with open(tmp_path / "ticket_TKT-001.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["ticket_id"] == "TKT-001"
        assert data["category"] == "Incidente"
        assert data["urgency"] == 3

    def test_emit_cria_csv_quando_nao_existe(self, state_valid, tmp_path, monkeypatch):
        """Quando o CSV não existe, ele deve ser criado com cabeçalho."""
        from nodes.emit import emit
        import nodes.emit as emit_module

        csv_path = tmp_path / "report.csv"
        monkeypatch.setattr(emit_module, "RESPONSES_DIR", tmp_path)
        monkeypatch.setattr(emit_module, "REPORT_CSV", csv_path)

        assert not csv_path.exists()
        emit(state_valid)
        assert csv_path.exists()

    def test_emit_closing_message_contem_contato(self, state_valid, tmp_path, monkeypatch):
        """A mensagem de encerramento deve conter informações de contato."""
        from nodes.emit import emit
        import nodes.emit as emit_module

        monkeypatch.setattr(emit_module, "RESPONSES_DIR", tmp_path)
        monkeypatch.setattr(emit_module, "REPORT_CSV", tmp_path / "report.csv")

        result = emit(state_valid)

        assert "agetic" in result["closing_message"].lower() or \
                "suporte" in result["closing_message"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# 6.  NÓ: queue_only
# ─────────────────────────────────────────────────────────────────────────────

class TestQueueOnlyNode:
    """
    Testa o nó `queue_only`.
    Usa tmp_path do pytest para evitar escrita no arquivo real da fila.
    """

    def test_queue_only_retorna_draft_fila_humana(self, state_valid, tmp_path, monkeypatch):
        """O nó deve marcar response_draft como mensagem de fila humana."""
        from nodes.queue_only import queue_only
        import nodes.queue_only as queue_module

        monkeypatch.setattr(queue_module, "QUEUE_PATH", tmp_path / "queue.json")

        result = queue_only(state_valid)

        assert "[FILA HUMANA]" in result["response"]["response_draft"]

    def test_queue_only_cria_arquivo_se_inexistente(self, state_valid, tmp_path, monkeypatch):
        """Quando human_queue.json não existe, deve ser criado com a entrada."""
        from nodes.queue_only import queue_only
        import nodes.queue_only as queue_module

        queue_path = tmp_path / "queue.json"
        monkeypatch.setattr(queue_module, "QUEUE_PATH", queue_path)

        assert not queue_path.exists()
        queue_only(state_valid)
        assert queue_path.exists()

        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

        assert len(queue) == 1
        assert queue[0]["ticket_id"] == "TKT-001"

    def test_queue_only_acumula_entradas(self, state_valid, tmp_path, monkeypatch):
        """Chamadas sucessivas devem acumular entradas na fila (não sobrescrever)."""
        from nodes.queue_only import queue_only
        import nodes.queue_only as queue_module

        queue_path = tmp_path / "queue.json"
        monkeypatch.setattr(queue_module, "QUEUE_PATH", queue_path)

        queue_only(state_valid)

        # Segundo ticket
        state2 = {
            "ticket": {**state_valid["ticket"], "id": "TKT-002"},
            "response": state_valid["response"],
            "closing_message": None,
        }
        queue_only(state2)

        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

        assert len(queue) == 2

    def test_queue_only_entrada_tem_campos_obrigatorios(self, state_valid, tmp_path, monkeypatch):
        """A entrada na fila deve conter timestamp, ticket_id e reason."""
        from nodes.queue_only import queue_only
        import nodes.queue_only as queue_module

        queue_path = tmp_path / "queue.json"
        monkeypatch.setattr(queue_module, "QUEUE_PATH", queue_path)

        queue_only(state_valid)

        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

        entry = queue[0]
        assert "timestamp" in entry
        assert "ticket_id" in entry
        assert "reason" in entry

    def test_queue_only_preserva_campos_response(self, state_valid, tmp_path, monkeypatch):
        """Campos como category e resulting_priority devem ser preservados no retorno."""
        from nodes.queue_only import queue_only
        import nodes.queue_only as queue_module

        monkeypatch.setattr(queue_module, "QUEUE_PATH", tmp_path / "queue.json")

        result = queue_only(state_valid)

        assert result["response"]["category"] == state_valid["response"]["category"]
        assert result["response"]["resulting_priority"] == state_valid["response"]["resulting_priority"]
