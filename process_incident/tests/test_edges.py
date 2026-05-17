"""
test_edges.py — Testes Unitários das Arestas Condicionais (Conditional Edges)
==============================================================================
Projeto : Triagem de Incidentes de Segurança da Informação (AGETIC/ETIR/UFMS)

Estratégia
----------
• Cada função de roteamento é testada de forma isolada, passando diferentes
  dicionários de estado e verificando qual string de roteamento é retornada.
• Nenhum grafo é compilado. Não se usa builder.compile().
• Os testes verificam TODOS os caminhos de cada função de decisão.

Funções de roteamento cobertas
--------------------------------
  1. incident_validation  — Pós-ingest: emit_incident (falha) vs classify_criticality (ok)
"""

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES LOCAIS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def incident_base():
    return {
        "id": "INC-EDGE-001",
        "timestamp": "2026-03-10T07:42:00Z",
        "free_text": (
            "Recebi um e-mail suspeito pedindo para confirmar meus dados "
            "do Passaporte UFMS em um link externo."
        ),
        "validation_status": True,
        "category": "Phishing",
        "category_justification": "Tentativa de phishing.",
        "critical": False,
        "critical_justification": "Escopo limitado.",
        "scope": "Individual",
        "affected_systems": "Institutional Email",
        "responsible_person": "João Silva",
        "contact_info": "joao.silva@agetic.ufms.br",
        "containment_steps": [],
        "containment_justification": "",
        "alert_draft": "",
        "report_template": "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ARESTA CONDICIONAL: incident_validation
#    Localização: utilities/incident_validation.py
#    Usada em   : builder.add_conditional_edges("ingest_incident", incident_validation, ...)
#    Caminhos   : "emit_incident" | "classify_criticality"
# ═══════════════════════════════════════════════════════════════════════════════

class TestIncidentValidationEdge:
    """
    incident_validation(state) -> "emit_incident" | "classify_criticality"

    Regra de negócio:
      • Se incident.validation_status is False → "emit_incident"  (erro, encerra)
      • Qualquer outro caso                    → "classify_criticality"
    """

    def test_incident_validation_falha_retorna_emit_incident(self, incident_base):
        """validation_status=False → rota para 'emit_incident'."""
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": {**incident_base, "validation_status": False}}
        assert incident_validation(state) == "emit_incident"

    def test_incident_validation_sucesso_retorna_classify_criticality(self, incident_base):
        """validation_status=True → rota para 'classify_criticality'."""
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": {**incident_base, "validation_status": True}}
        assert incident_validation(state) == "classify_criticality"

    def test_incident_validation_chave_ausente_retorna_classify_criticality(self, incident_base):
        """Sem validation_status no incident → default → 'classify_criticality'."""
        from process_incident.utilities.incident_validation import incident_validation

        incident = dict(incident_base)
        incident.pop("validation_status", None)

        state = {"incident": incident}
        assert incident_validation(state) == "classify_criticality"

    def test_incident_validation_incident_vazio_retorna_classify_criticality(self):
        """incident={} → validation_status ausente → 'classify_criticality'."""
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": {}}
        assert incident_validation(state) == "classify_criticality"

    def test_incident_validation_incident_none_retorna_classify_criticality(self):
        """incident=None → não deve explodir, deve rotear para 'classify_criticality'."""
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": None}
        assert incident_validation(state) == "classify_criticality"

    def test_incident_validation_status_false_com_estado_completo(self, incident_base):
        """Estado completo mas validation_status=False → 'emit_incident'."""
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": {**incident_base, "validation_status": False}}
        assert incident_validation(state) == "emit_incident"

    def test_incident_validation_retorna_apenas_strings_validas(self, incident_base):
        """O retorno deve ser sempre uma das duas strings esperadas."""
        from process_incident.utilities.incident_validation import incident_validation

        rotas_validas = {"emit_incident", "classify_criticality"}

        cenarios = [
            True,
            False,
            None,
        ]

        for status in cenarios:
            incident = dict(incident_base)
            if status is None:
                incident.pop("validation_status", None)
            else:
                incident["validation_status"] = status

            state = {"incident": incident}
            result = incident_validation(state)
            assert result in rotas_validas, (
                f"Rota inesperada '{result}' para validation_status={status}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TESTES DE INTEGRAÇÃO LEVE: fluxos completos de roteamento
#    Verifica sequências encadeadas sem compilar o grafo.
# ═══════════════════════════════════════════════════════════════════════════════

class TestFluxosDeRoteamento:
    """
    Testa sequências de roteamento encadeadas sem compilar o grafo.
    Confirma que a combinação de decisões produz o caminho correto.
    """

    def test_fluxo_incidente_invalido_vai_direto_para_emit(self, incident_base):
        """
        Incidente com validation_status=False após ingest deve ir direto
        para emit_incident, ignorando toda a cadeia de triagem.
        """
        from process_incident.utilities.incident_validation import incident_validation

        state_pos_ingest = {"incident": {**incident_base, "validation_status": False}}
        assert incident_validation(state_pos_ingest) == "emit_incident"

    def test_fluxo_incidente_valido_vai_para_classify_criticality(self, incident_base):
        """
        Incidente com validation_status=True após ingest deve seguir:
        ingest_incident → classify_criticality → lookup_owner → ...
        """
        from process_incident.utilities.incident_validation import incident_validation

        state_pos_ingest = {"incident": {**incident_base, "validation_status": True}}
        assert incident_validation(state_pos_ingest) == "classify_criticality"

    def test_fluxo_incidente_sem_free_text_curto_circuita_em_emit(self):
        """
        Incidente com free_text de 1 caractere deve falhar no ingest
        (validation_status=False) e ir direto para emit_incident.
        """
        from process_incident.core.nodes.ingest_incident import ingest_incident
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": {
            "id": "INC-FLOW-001",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "x",  # inválido
        }}

        result_ingest = ingest_incident(state)
        assert result_ingest["incident"]["validation_status"] is False

        rota = incident_validation(result_ingest)
        assert rota == "emit_incident"

    def test_fluxo_incidente_valido_passa_pelo_classify(self):
        """
        Incidente válido deve passar pelo ingest com validation_status=True
        e ser roteado para classify_criticality.
        """
        from process_incident.core.nodes.ingest_incident import ingest_incident
        from process_incident.utilities.incident_validation import incident_validation

        state = {"incident": {
            "id": "INC-FLOW-002",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "Detectamos acesso não autorizado ao servidor de arquivos.",
        }}

        result_ingest = ingest_incident(state)
        assert result_ingest["incident"]["validation_status"] is True

        rota = incident_validation(result_ingest)
        assert rota == "classify_criticality"