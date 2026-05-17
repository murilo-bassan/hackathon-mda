"""
test_edges.py — Testes Unitários das Arestas Condicionais (Conditional Edges)
==============================================================================
Projeto : Triagem de Chamados de TIC (AGETIC/UFMS)

Estratégia
----------
• Cada função de roteamento é testada de forma isolada, passando diferentes
  dicionários de estado e verificando qual string de roteamento é retornada.
• Nenhum grafo é compilado. Não se usa app.compile().
• Os testes verificam TODOS os caminhos de cada função de decisão.

Funções de roteamento cobertas
--------------------------------
  1. validation_response  — Pós-ingest: emit (falha) vs validate_input (ok)
  2. decide_content       — Pós-validate_input: draft_request vs classify_type
  3. decide_response      — Pós-score_priority: draft_response vs queue_only
"""

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES LOCAIS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def ticket_base():
    return {
        "id": "TKT-EDGE-001",
        "timestamp": "2025-05-14T10:00:00",
        "channel": "sistema de chamados",
        "requester_profile": "professor",
        "free_text": "Impressora não funciona.",
        "needs_more_info": False,
        "info_justification": "",
    }


@pytest.fixture
def response_base():
    return {
        "ticket_id": "TKT-EDGE-001",
        "category": "Requisição",
        "category_justification": "Pedido de instalação.",
        "urgency": 2,
        "impact": 2,
        "resulting_priority": 2,
        "priority_justification": "Baixa urgência.",
        "service_type": "Suporte de Campo",
        "support_level": 1,
        "department": "N1 - Atendimento",
        "response_draft": "",
        "validation_status": True,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ARESTA CONDICIONAL: validation_response
#    Localização: utilities/validation_response.py
#    Usada em   : builder.add_conditional_edges("ingest", validation_response, ...)
#    Caminhos   : "emit" | "validate_input"
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidationResponseEdge:
    """
    validation_response(state) -> "emit" | "validate_input"

    Regra de negócio:
      • Se response.validation_status is False  → "emit"  (erro de validação, encerra)
      • Qualquer outro caso                     → "validate_input"
    """

    def test_validation_response_falha_retorna_emit(self, ticket_base):
        """validation_status=False → rota para 'emit'."""
        from process_request.utilities.validation_response import validation_response

        state = {
            "ticket": ticket_base,
            "response": {"validation_status": False},
            "closing_message": None,
        }
        assert validation_response(state) == "emit"

    def test_validation_response_sucesso_retorna_validate_input(self, ticket_base):
        """validation_status=True → rota para 'validate_input'."""
        from process_request.utilities.validation_response import validation_response

        state = {
            "ticket": ticket_base,
            "response": {"validation_status": True},
            "closing_message": None,
        }
        assert validation_response(state) == "validate_input"

    def test_validation_response_ausente_retorna_validate_input(self, ticket_base):
        """Sem validation_status no response → rota para 'validate_input' (default)."""
        from process_request.utilities.validation_response import validation_response

        state = {
            "ticket": ticket_base,
            "response": {},   # chave ausente
            "closing_message": None,
        }
        assert validation_response(state) == "validate_input"

    def test_validation_response_response_none_retorna_validate_input(self, ticket_base):
        """response=None → não deve explodir, deve rotear para 'validate_input'."""
        from process_request.utilities.validation_response import validation_response

        state = {
            "ticket": ticket_base,
            "response": None,   # Edge case
            "closing_message": None,
        }
        assert validation_response(state) == "validate_input"

    def test_validation_response_status_true_explicito(self, ticket_base, response_base):
        """Estado completo com validation_status=True → 'validate_input'."""
        from process_request.utilities.validation_response import validation_response

        state = {
            "ticket": ticket_base,
            "response": response_base,  # validation_status=True
            "closing_message": None,
        }
        assert validation_response(state) == "validate_input"

    def test_validation_response_status_false_com_estado_completo(
        self, ticket_base, response_base
    ):
        """Estado completo mas validation_status=False → 'emit'."""
        from process_request.utilities.validation_response import validation_response

        response = dict(response_base)
        response["validation_status"] = False

        state = {
            "ticket": ticket_base,
            "response": response,
            "closing_message": None,
        }
        assert validation_response(state) == "emit"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ARESTA CONDICIONAL: decide_content
#    Localização: utilities/decide_content.py
#    Usada em   : builder.add_conditional_edges("validate_input", decide_content, ...)
#    Caminhos   : "draft_request" | "classify_type"
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecideContentEdge:
    """
    decide_content(state) -> "draft_request" | "classify_type"

    Regra de negócio:
      • ticket.needs_more_info is True  → "draft_request"
      • ticket.needs_more_info is False → "classify_type"
    """

    def test_decide_content_needs_more_info_true_retorna_draft_request(
        self, ticket_base, response_base
    ):
        """needs_more_info=True → 'draft_request'."""
        from process_request.utilities.decide_content import decide_content

        ticket = dict(ticket_base)
        ticket["needs_more_info"] = True

        state = {
            "ticket": ticket,
            "response": response_base,
            "closing_message": None,
        }
        assert decide_content(state) == "draft_request"

    def test_decide_content_needs_more_info_false_retorna_classify_type(
        self, ticket_base, response_base
    ):
        """needs_more_info=False → 'classify_type'."""
        from process_request.utilities.decide_content import decide_content

        ticket = dict(ticket_base)
        ticket["needs_more_info"] = False

        state = {
            "ticket": ticket,
            "response": response_base,
            "closing_message": None,
        }
        assert decide_content(state) == "classify_type"

    def test_decide_content_chave_ausente_retorna_classify_type(self, response_base):
        """Sem a chave needs_more_info → default False → 'classify_type'."""
        from process_request.utilities.decide_content import decide_content

        state = {
            "ticket": {},   # chave ausente
            "response": response_base,
            "closing_message": None,
        }
        assert decide_content(state) == "classify_type"

    def test_decide_content_ticket_ausente_retorna_classify_type(self, response_base):
        """Sem a chave 'ticket' no state → 'classify_type'."""
        from process_request.utilities.decide_content import decide_content

        state = {
            "response": response_base,
            "closing_message": None,
        }
        assert decide_content(state) == "classify_type"

    def test_decide_content_retorna_apenas_strings_validas(self, ticket_base, response_base):
        """O retorno deve ser sempre uma das duas strings esperadas."""
        from process_request.utilities.decide_content import decide_content

        valid_routes = {"draft_request", "classify_type"}

        for needs_more in [True, False]:
            ticket = dict(ticket_base)
            ticket["needs_more_info"] = needs_more
            state = {"ticket": ticket, "response": response_base, "closing_message": None}
            assert decide_content(state) in valid_routes


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ARESTA CONDICIONAL: decide_response
#    Localização: utilities/decide_response.py
#    Usada em   : builder.add_conditional_edges("score_priority", decide_response_from_state, ...)
#    Caminhos   : "draft_response" | "queue_only"
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecideResponseEdge:
    """
    decide_response_from_state(state) -> "draft_response" | "queue_only"

    Regra de negócio (conforme utilities/decide_response.py):
      • resulting_priority <= 3  AND  category normalizada == "requisicao"
          → "draft_response"  (automatiza a resposta)
      • resulting_priority <= 2  AND  category normalizada == "incidente"
          → "draft_response"  (automatiza incidentes de baixíssima prioridade)
      • Qualquer outro caso
          → "queue_only"  (escala para humano)

    Normalização: acento removido, lowercase, strip
      ex: "Requisição" → "requisicao"

    NOTA: a função que recebe state é `decide_response_from_state`.
    """

    # ── Caminho "draft_response" — Requisição ─────────────────────────────────

    def test_decide_response_requisicao_prioridade_1_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='Requisição', prioridade=1 → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    def test_decide_response_requisicao_prioridade_2_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='Requisição', prioridade=2 → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 2, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    def test_decide_response_requisicao_prioridade_3_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='Requisição', prioridade=3 (limite exato) → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 3, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    def test_decide_response_requisicao_sem_acento_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='requisicao' (sem acento), prioridade=1 → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1, "category": "requisicao"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    def test_decide_response_requisicao_maiuscula_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='REQUISIÇÃO' (maiúscula com acento), prioridade=1 → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1, "category": "REQUISIÇÃO"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    def test_decide_response_categoria_com_espacos_e_acentos_retorna_draft_response(
        self, ticket_base
    ):
        """'  Requisição  ' (com espaços) → normalização → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1, "category": "  Requisição  "},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    # ── Caminho "draft_response" — Incidente de baixa prioridade ─────────────

    def test_decide_response_incidente_prioridade_1_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='Incidente', prioridade=1 → 'draft_response' (incidente leve)."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1, "category": "Incidente"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    def test_decide_response_incidente_prioridade_2_retorna_draft_response(
        self, ticket_base
    ):
        """categoria='Incidente', prioridade=2 (limite exato) → 'draft_response'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 2, "category": "Incidente"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"

    # ── Caminho "queue_only" ──────────────────────────────────────────────────

    def test_decide_response_incidente_prioridade_3_retorna_queue_only(self, ticket_base):
        """categoria='Incidente', prioridade=3 (acima do limiar) → 'queue_only'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 3, "category": "Incidente"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_incidente_alta_prioridade_retorna_queue_only(self, ticket_base):
        """categoria='Incidente', prioridade=5 → 'queue_only'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 5, "category": "Incidente"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_requisicao_prioridade_4_retorna_queue_only(
        self, ticket_base
    ):
        """categoria='Requisição', prioridade=4 (acima do limiar) → 'queue_only'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 4, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_requisicao_prioridade_5_retorna_queue_only(
        self, ticket_base
    ):
        """categoria='Requisição', prioridade=5 (máxima) → 'queue_only'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 5, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_categoria_vazia_retorna_queue_only(self, ticket_base):
        """categoria='' → 'queue_only' (não satisfaz nenhuma condição)."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1, "category": ""},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_sem_categoria_retorna_queue_only(self, ticket_base):
        """Sem chave 'category' no response → 'queue_only'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 1},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_sem_prioridade_retorna_queue_only(self, ticket_base):
        """Sem 'resulting_priority' → default 99 → 'queue_only'."""
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "queue_only"

    def test_decide_response_retorna_apenas_strings_validas(self, ticket_base):
        """O retorno deve ser sempre uma das duas strings esperadas."""
        from process_request.utilities.decide_response import decide_response_from_state

        valid_routes = {"draft_response", "queue_only"}

        cenarios = [
            {"resulting_priority": 1, "category": "Requisição"},
            {"resulting_priority": 2, "category": "Requisição"},
            {"resulting_priority": 3, "category": "Requisição"},
            {"resulting_priority": 4, "category": "Requisição"},
            {"resulting_priority": 1, "category": "Incidente"},
            {"resulting_priority": 2, "category": "Incidente"},
            {"resulting_priority": 3, "category": "Incidente"},
            {"resulting_priority": 5, "category": "Incidente"},
            {"resulting_priority": 1, "category": ""},
            {"resulting_priority": 99},   # sem category
        ]

        for response in cenarios:
            state = {"ticket": ticket_base, "response": response, "closing_message": None}
            result = decide_response_from_state(state)
            assert result in valid_routes, (
                f"Rota inesperada '{result}' para response={response}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TESTES DE INTEGRAÇÃO LEVE: fluxos completos de roteamento
#    Verifica sequências de chamadas aos roteadores encadeados
# ═══════════════════════════════════════════════════════════════════════════════

class TestFluxosDeRoteamento:
    """
    Testa sequências de roteamento encadeadas sem compilar o grafo.
    Confirma que a combinação de decisões produz o caminho correto.
    """

    def test_fluxo_ticket_invalido_vai_direto_para_emit(self, ticket_base):
        """
        Ticket com validation_status=False após ingest deve ir direto para emit,
        ignorando toda a cadeia de classificação.
        """
        from process_request.utilities.validation_response import validation_response

        state_pos_ingest = {
            "ticket": ticket_base,
            "response": {"validation_status": False},
            "closing_message": None,
        }
        assert validation_response(state_pos_ingest) == "emit"

    def test_fluxo_ticket_incompleto_vai_para_draft_request(self, ticket_base):
        """
        Ticket válido mas incompleto (needs_more_info=True) deve seguir:
        ingest → validate_input → draft_request → emit
        """
        from process_request.utilities.validation_response import validation_response
        from process_request.utilities.decide_content import decide_content

        # Pós-ingest: validação estrutural OK
        state_pos_ingest = {
            "ticket": ticket_base,
            "response": {"validation_status": True},
            "closing_message": None,
        }
        assert validation_response(state_pos_ingest) == "validate_input"

        # Pós-validate_input: LLM pediu mais informações
        ticket_with_flag = dict(ticket_base)
        ticket_with_flag["needs_more_info"] = True

        state_pos_validate = {
            "ticket": ticket_with_flag,
            "response": {"validation_status": True},
            "closing_message": None,
        }
        assert decide_content(state_pos_validate) == "draft_request"

    def test_fluxo_requisicao_baixa_prioridade_vai_para_draft_response(
        self, ticket_base
    ):
        """
        Fluxo de requisição simples com prioridade baixa:
        ingest → validate_input → classify_type → score_priority → draft_response → emit
        """
        from process_request.utilities.validation_response import validation_response
        from process_request.utilities.decide_content import decide_content
        from process_request.utilities.decide_response import decide_response_from_state

        # Pós-ingest: OK
        state_pos_ingest = {
            "ticket": ticket_base,
            "response": {"validation_status": True},
            "closing_message": None,
        }
        assert validation_response(state_pos_ingest) == "validate_input"

        # Pós-validate_input: ticket completo
        ticket_completo = dict(ticket_base)
        ticket_completo["needs_more_info"] = False

        state_pos_validate = {
            "ticket": ticket_completo,
            "response": {"validation_status": True},
            "closing_message": None,
        }
        assert decide_content(state_pos_validate) == "classify_type"

        # Pós-score_priority: requisição de baixa prioridade (<=3)
        state_pos_score = {
            "ticket": ticket_completo,
            "response": {"resulting_priority": 2, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state_pos_score) == "draft_response"

    def test_fluxo_incidente_alta_prioridade_vai_para_queue_only(
        self, ticket_base
    ):
        """
        Fluxo de incidente crítico:
        ingest → validate_input → classify_type → score_priority → queue_only → emit
        """
        from process_request.utilities.validation_response import validation_response
        from process_request.utilities.decide_content import decide_content
        from process_request.utilities.decide_response import decide_response_from_state

        # Pós-ingest: OK
        assert validation_response({
            "ticket": ticket_base,
            "response": {"validation_status": True},
            "closing_message": None,
        }) == "validate_input"

        # Pós-validate_input: completo
        ticket_completo = dict(ticket_base)
        ticket_completo["needs_more_info"] = False

        assert decide_content({
            "ticket": ticket_completo,
            "response": {"validation_status": True},
            "closing_message": None,
        }) == "classify_type"

        # Pós-score_priority: incidente crítico (prioridade 5 > limiar 2)
        assert decide_response_from_state({
            "ticket": ticket_completo,
            "response": {"resulting_priority": 5, "category": "Incidente"},
            "closing_message": None,
        }) == "queue_only"

    def test_fluxo_requisicao_prioridade_limite_3_vai_para_draft_response(
        self, ticket_base
    ):
        """
        Requisição com prioridade exatamente 3 (limite máximo permitido) deve
        seguir para draft_response, não queue_only.
        """
        from process_request.utilities.decide_response import decide_response_from_state

        state = {
            "ticket": ticket_base,
            "response": {"resulting_priority": 3, "category": "Requisição"},
            "closing_message": None,
        }
        assert decide_response_from_state(state) == "draft_response"