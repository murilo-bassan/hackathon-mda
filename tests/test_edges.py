"""
Suíte de Testes Unitários — Arestas Condicionais (Conditional Edges)
====================================================================
Projeto : Triagem de Chamados de TIC (AGETIC/UFMS)
Arquivo : test_edges.py
Cobertura: validation_response | decide_response | normalize_str

As funções de roteamento são testadas como puras:
recebem um State e retornam uma string com o nome do próximo nó.
Nenhum grafo é compilado.

Execução:
    pytest tests/test_edges.py -v
"""

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# 1.  ARESTA CONDICIONAL: validation_response
#     Rota saída de `ingest` → "classify_type" ou "emit"
# ─────────────────────────────────────────────────────────────────────────────

class TestValidationResponseEdge:
    """
    validation_response(state) -> str
    ─────────────────────────────────
    Regra: se response.validation_status is False → "emit"
        caso contrário (True ou ausente)          → "classify_type"
    """

    def test_validation_true_vai_para_classify_type(self):
        """validation_status=True → próximo nó deve ser 'classify_type'."""
        from utilities.validation_response import validation_response

        state = {"response": {"validation_status": True}}
        assert validation_response(state) == "classify_type"

    def test_validation_false_vai_para_emit(self):
        """validation_status=False (ticket inválido) → próximo nó deve ser 'emit'."""
        from utilities.validation_response import validation_response

        state = {"response": {"validation_status": False}}
        assert validation_response(state) == "emit"

    def test_validation_status_ausente_vai_para_classify_type(self):
        """Sem a chave validation_status no response → considera válido → 'classify_type'."""
        from utilities.validation_response import validation_response

        state = {"response": {}}
        assert validation_response(state) == "classify_type"

    def test_validation_response_none_vai_para_classify_type(self):
        """response=None → deve se comportar como válido e retornar 'classify_type'."""
        from utilities.validation_response import validation_response

        state = {"response": None}
        assert validation_response(state) == "classify_type"

    def test_validation_sem_chave_response_vai_para_classify_type(self):
        """Estado sem a chave 'response' → deve retornar 'classify_type' sem levantar exceção."""
        from utilities.validation_response import validation_response

        state = {}
        assert validation_response(state) == "classify_type"

    def test_validation_status_none_vai_para_classify_type(self):
        """validation_status=None não é False → deve seguir o fluxo normal."""
        from utilities.validation_response import validation_response

        state = {"response": {"validation_status": None}}
        # None is not False → elif branch → classify_type
        assert validation_response(state) == "classify_type"

    def test_validation_retorna_string(self):
        """O retorno deve sempre ser uma string (nome de nó)."""
        from utilities.validation_response import validation_response

        for status in [True, False]:
            state = {"response": {"validation_status": status}}
            result = validation_response(state)
            assert isinstance(result, str), f"Esperado str, recebido {type(result)}"


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ARESTA CONDICIONAL: decide_response
#     Rota saída de `score_priority` → "draft_response" ou "queue_only"
# ─────────────────────────────────────────────────────────────────────────────

class TestDecideResponseEdge:
    """
    decide_response(state) -> str
    ──────────────────────────────
    Regra de negócio:
        prioridade <= 2  E  categoria == "requisição"  →  "draft_response"
        qualquer outra combinação                      →  "queue_only"
    """

    def _state(self, prioridade: int, categoria: str) -> dict:
        return {
            "response": {
                "resulting_priority": prioridade,
                "category": categoria,
            }
        }

    # ── Caso: deve ir para draft_response ────────────────────────────────────

    def test_prioridade_1_requisicao_vai_para_draft(self):
        """Prioridade 1 + Requisição → 'draft_response'."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(1, "Requisição")) == "draft_response"

    def test_prioridade_2_requisicao_vai_para_draft(self):
        """Prioridade 2 + Requisição (limite máximo) → 'draft_response'."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(2, "Requisição")) == "draft_response"

    def test_categoria_minuscula_vai_para_draft(self):
        """Categoria em minúsculas deve ser normalizada e reconhecida."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(1, "requisição")) == "draft_response"

    def test_categoria_maiuscula_vai_para_draft(self):
        """Categoria em maiúsculas deve ser normalizada e reconhecida."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(2, "REQUISIÇÃO")) == "draft_response"

    def test_categoria_com_acentuacao_alternativa(self):
        """Categoria 'Requisicao' (sem til) deve ser reconhecida via normalize_str."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(1, "Requisicao")) == "draft_response"

    # ── Caso: deve ir para queue_only ────────────────────────────────────────

    def test_prioridade_3_requisicao_vai_para_queue(self):
        """Prioridade 3 (acima do limiar) + Requisição → 'queue_only'."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(3, "Requisição")) == "queue_only"

    def test_prioridade_4_vai_para_queue(self):
        """Prioridade alta (4) → 'queue_only', independente da categoria."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(4, "Requisição")) == "queue_only"

    def test_prioridade_5_vai_para_queue(self):
        """Prioridade máxima (5) → 'queue_only' (fail-safe do LLM)."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(5, "Incidente")) == "queue_only"

    def test_categoria_incidente_vai_para_queue(self):
        """Categoria 'Incidente' nunca vai para draft_response."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(1, "Incidente")) == "queue_only"

    def test_categoria_indefinida_vai_para_queue(self):
        """Categoria 'Indefinida' (default do classify) → 'queue_only'."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(1, "Indefinida")) == "queue_only"

    def test_prioridade_ausente_usa_99_e_vai_para_queue(self):
        """Sem resulting_priority no estado → default 99 → 'queue_only'."""
        from utilities.decide_response import decide_response

        state = {"response": {"category": "Requisição"}}
        assert decide_response(state) == "queue_only"

    def test_categoria_ausente_vai_para_queue(self):
        """Sem 'category' no estado → default '' → não é 'requisição' → 'queue_only'."""
        from utilities.decide_response import decide_response

        state = {"response": {"resulting_priority": 1}}
        assert decide_response(state) == "queue_only"

    def test_response_vazio_vai_para_queue(self):
        """Estado com response={} → defaults extremos → 'queue_only'."""
        from utilities.decide_response import decide_response

        state = {"response": {}}
        assert decide_response(state) == "queue_only"

    def test_decide_retorna_string(self):
        """O retorno deve sempre ser uma string."""
        from utilities.decide_response import decide_response

        for prio, cat in [(1, "Requisição"), (5, "Incidente"), (3, "")]:
            result = decide_response({"response": {"resulting_priority": prio, "category": cat}})
            assert isinstance(result, str)

    # ── Testes de valores limite (boundary) ──────────────────────────────────

    def test_limite_exato_2_requisicao_draft(self):
        """Exatamente no limiar 2 → 'draft_response' (≤ 2 é inclusivo)."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(2, "Requisição")) == "draft_response"

    def test_limite_exato_3_queue(self):
        """Exatamente no limiar 3 → 'queue_only' (> 2)."""
        from utilities.decide_response import decide_response

        assert decide_response(self._state(3, "Requisição")) == "queue_only"


# ─────────────────────────────────────────────────────────────────────────────
# 3.  UTILITÁRIO: normalize_str
#     Usado internamente por decide_response para normalizar categorias
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeStr:
    """Testa a função auxiliar de normalização de strings."""

    def test_remove_acentos(self):
        """Deve remover acentos (NFKD + ascii ignore)."""
        from utilities.decide_response import normalize_str

        assert normalize_str("Requisição") == "requisicao"

    def test_converte_para_minusculo(self):
        from utilities.decide_response import normalize_str

        assert normalize_str("INCIDENTE") == "incidente"

    def test_remove_espacos_laterais(self):
        from utilities.decide_response import normalize_str

        assert normalize_str("  Requisição  ") == "requisicao"

    def test_string_vazia(self):
        from utilities.decide_response import normalize_str

        assert normalize_str("") == ""

    def test_sem_acentos_retorna_minusculo(self):
        from utilities.decide_response import normalize_str

        assert normalize_str("Incidente") == "incidente"


# ─────────────────────────────────────────────────────────────────────────────
# 4.  TESTE DE INTEGRAÇÃO LEVE — sequência de roteamento completa
#     (sem compilar o grafo, apenas encadeando as funções de rota)
# ─────────────────────────────────────────────────────────────────────────────

class TestRoutingSequence:
    """
    Verifica que a cadeia de roteamento produz o caminho esperado
    para diferentes cenários de estado, sem instanciar o StateGraph.
    """

    def test_caminho_feliz_requisicao_baixa_prioridade(self):
        """
        Ticket válido + Requisição + Prioridade 1
        → ingest OK → classify_type → score_priority → draft_response → emit
        """
        from utilities.validation_response import validation_response
        from utilities.decide_response import decide_response

        state_apos_ingest = {
            "response": {"validation_status": True},
        }
        assert validation_response(state_apos_ingest) == "classify_type"

        state_apos_score = {
            "response": {
                "resulting_priority": 1,
                "category": "Requisição",
            }
        }
        assert decide_response(state_apos_score) == "draft_response"

    def test_caminho_ticket_invalido_vai_direto_emit(self):
        """
        Ticket inválido → ingest falha → validation_response → emit (sem passar por classify)
        """
        from utilities.validation_response import validation_response

        state_apos_ingest = {
            "response": {"validation_status": False},
        }
        assert validation_response(state_apos_ingest) == "emit"

    def test_caminho_incidente_alta_prioridade_vai_para_fila(self):
        """
        Ticket válido + Incidente + Prioridade 5 (fail-safe LLM)
        → classify_type → score_priority → queue_only
        """
        from utilities.validation_response import validation_response
        from utilities.decide_response import decide_response

        state_apos_ingest = {"response": {"validation_status": True}}
        assert validation_response(state_apos_ingest) == "classify_type"

        state_apos_score = {
            "response": {
                "resulting_priority": 5,
                "category": "Incidente",
            }
        }
        assert decide_response(state_apos_score) == "queue_only"

    def test_caminho_requisicao_prioridade_alta_vai_para_fila(self):
        """
        Mesmo sendo Requisição, prioridade 4 → queue_only (analista humano).
        """
        from utilities.decide_response import decide_response

        state = {"response": {"resulting_priority": 4, "category": "Requisição"}}
        assert decide_response(state) == "queue_only"
