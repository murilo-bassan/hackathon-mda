"""
test_nodes.py — Testes Unitários dos Nós do Grafo LangGraph
============================================================
Projeto : Triagem de Incidentes de Segurança da Informação (AGETIC/ETIR/UFMS)

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
  1. ingest_incident        — Validação Pydantic do incidente bruto
  2. classify_criticality   — Classificação de criticidade via LLM
  3. lookup_owner           — Busca determinística do responsável técnico
  4. recommend_containment  — Recomendação de contenção via LLM + playbook
  5. draft_alert            — Geração do e-mail de alerta via LLM
  6. request_report         — Geração do template de relatório parcial via LLM
  7. emit_incident          — Persistência em JSON e CSV
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open


# ═══════════════════════════════════════════════════════════════════════════════
# 1. NÓ: ingest_incident
# ═══════════════════════════════════════════════════════════════════════════════

class TestIngestIncidentNode:
    """Testa o nó `ingest_incident` que valida e normaliza o incidente de entrada."""

    def test_ingest_incident_valido_retorna_validation_status_true(self, valid_incident):
        """Com um incidente válido, deve retornar validation_status=True."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "id": "INC-TEST-001",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "Recebi um e-mail suspeito pedindo minha senha institucional.",
        }}
        result = ingest_incident(state)

        assert "incident" in result
        assert result["incident"]["validation_status"] is True

    def test_ingest_incident_valido_preserva_id(self):
        """O id do incidente deve ser preservado após o ingest."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "id": "INC-TEST-001",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "Tentativa de acesso não autorizado ao sistema.",
        }}
        result = ingest_incident(state)

        assert result["incident"]["id"] == "INC-TEST-001"

    def test_ingest_incident_sem_id_gera_uuid(self):
        """Incidente sem 'id' deve receber um UUID gerado automaticamente."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "Suspeita de malware no laboratório de informática.",
        }}
        result = ingest_incident(state)

        assert "id" in result["incident"]
        assert len(result["incident"]["id"]) > 0

    def test_ingest_incident_invalido_sem_free_text(self):
        """Incidente sem 'free_text' deve falhar validação com validation_status=False."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "id": "INC-BAD-001",
            "timestamp": "2026-03-10T07:42:00Z",
            # free_text ausente propositalmente
        }}
        result = ingest_incident(state)

        assert result["incident"]["validation_status"] is False

    def test_ingest_incident_invalido_free_text_curto(self):
        """free_text com menos de 2 caracteres deve falhar validação."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "id": "INC-BAD-002",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "x",  # min_length=2
        }}
        result = ingest_incident(state)

        assert result["incident"]["validation_status"] is False

    def test_ingest_incident_invalido_sem_timestamp(self):
        """Incidente sem 'timestamp' deve falhar validação."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "id": "INC-BAD-003",
            "free_text": "Detectamos acesso suspeito ao servidor de arquivos.",
        }}
        result = ingest_incident(state)

        assert result["incident"]["validation_status"] is False

    def test_ingest_incident_invalido_alert_draft_contem_json_erro(self):
        """Em caso de ValidationError, alert_draft deve conter o JSON do erro."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {
            "id": "INC-ERR-001",
            # free_text e timestamp ausentes
        }}
        result = ingest_incident(state)

        assert isinstance(result["incident"]["alert_draft"], str)
        errors = json.loads(result["incident"]["alert_draft"])
        assert isinstance(errors, list)

    def test_ingest_incident_estado_vazio_nao_quebra(self):
        """Estado com incident={} não deve levantar exceção."""
        from process_incident.core.nodes.ingest_incident import ingest_incident

        state = {"incident": {}}
        result = ingest_incident(state)

        assert "incident" in result
        assert result["incident"]["validation_status"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. NÓ: classify_criticality
# ═══════════════════════════════════════════════════════════════════════════════

class TestClassifyCriticalityNode:
    """Testa o nó `classify_criticality` que classifica a criticidade via LLM."""

    @patch("process_incident.core.nodes.classify_criticality.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.classify_criticality.call_llm")
    def test_classify_criticality_retorna_campos_corretos(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O update deve conter critical, category, scope e affected_systems."""
        from process_incident.core.nodes.classify_criticality import classify_criticality

        mock_call_llm.return_value = {
            "critical": True,
            "justification": "Sistema crítico afetado.",
            "category": "Indisponibilidade",
            "category_justification": "Servidor fora do ar.",
            "scope": "Institucional",
            "affected_systems": "LDAP Authentication Server",
        }

        result = classify_criticality(base_state)

        assert "incident" in result
        assert result["incident"]["critical"] is True
        assert result["incident"]["category"] == "Indisponibilidade"
        assert result["incident"]["scope"] == "Institucional"
        assert result["incident"]["affected_systems"] == "LDAP Authentication Server"

    @patch("process_incident.core.nodes.classify_criticality.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.classify_criticality.call_llm")
    def test_classify_criticality_nao_critico(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """LLM indica não-crítico → critical=False."""
        from process_incident.core.nodes.classify_criticality import classify_criticality

        mock_call_llm.return_value = {
            "critical": False,
            "justification": "Escopo limitado.",
            "category": "Phishing",
            "category_justification": "Tentativa de phishing isolada.",
            "scope": "Individual",
            "affected_systems": "Institutional Email",
        }

        result = classify_criticality(base_state)

        assert result["incident"]["critical"] is False

    @patch("process_incident.core.nodes.classify_criticality.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.classify_criticality.call_llm")
    def test_classify_criticality_llm_retorna_vazio_usa_defaults(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} deve usar os valores default."""
        from process_incident.core.nodes.classify_criticality import classify_criticality

        mock_call_llm.return_value = {}

        result = classify_criticality(base_state)

        assert result["incident"]["critical"] is False
        assert result["incident"]["category"] == "Indefinida"
        assert result["incident"]["scope"] == "Indefinido"
        assert result["incident"]["affected_systems"] == "indefinido"

    @patch("process_incident.core.nodes.classify_criticality.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.classify_criticality.call_llm")
    def test_classify_criticality_preserva_campos_existentes(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos pré-existentes no incident (id, free_text) devem ser preservados."""
        from process_incident.core.nodes.classify_criticality import classify_criticality

        mock_call_llm.return_value = {
            "critical": False,
            "justification": "OK.",
            "category": "Phishing",
            "category_justification": "Phishing.",
            "scope": "Individual",
            "affected_systems": "Email",
        }

        result = classify_criticality(base_state)

        assert result["incident"]["id"] == "INC-TEST-001"
        assert "free_text" in result["incident"]

    @patch("process_incident.core.nodes.classify_criticality.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.classify_criticality.call_llm")
    def test_classify_criticality_chama_llm_com_free_text(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O free_text do incidente deve ser passado para o call_llm."""
        from process_incident.core.nodes.classify_criticality import classify_criticality

        mock_call_llm.return_value = {
            "critical": False, "justification": "", "category": "Phishing",
            "category_justification": "", "scope": "", "affected_systems": "",
        }

        classify_criticality(base_state)

        # CORREÇÃO: call_llm é chamado com user_prompt como keyword argument,
        # não como argumento posicional — usar .kwargs em vez de [0][1]
        user_prompt = mock_call_llm.call_args.kwargs["user_prompt"]
        assert "Passaporte UFMS" in user_prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NÓ: lookup_owner
# ═══════════════════════════════════════════════════════════════════════════════

class TestLookupOwnerNode:
    """Testa o nó `lookup_owner` — busca determinística, sem LLM."""

    @patch("process_incident.core.nodes.lookup_owner.load_inventory")
    def test_lookup_owner_encontra_responsavel_por_sistema(
        self, mock_load_inventory, base_state, sample_inventory
    ):
        """Com sistema conhecido, deve retornar o responsável correto."""
        from process_incident.core.nodes.lookup_owner import lookup_owner

        mock_load_inventory.return_value = sample_inventory

        result = lookup_owner(base_state)

        assert result["incident"]["responsible_person"] == "João Silva"
        assert "joao.silva@agetic.ufms.br" in result["incident"]["contact_info"]

    @patch("process_incident.core.nodes.lookup_owner.load_inventory")
    def test_lookup_owner_encontra_por_alias(
        self, mock_load_inventory, sample_inventory
    ):
        """Sistema descrito por alias deve ser encontrado corretamente."""
        from process_incident.core.nodes.lookup_owner import lookup_owner

        mock_load_inventory.return_value = sample_inventory

        state = {"incident": {
            "id": "INC-ALIAS-001",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "Problema com o webmail.",
            "affected_systems": "webmail",
        }}

        result = lookup_owner(state)

        assert result["incident"]["responsible_person"] == "João Silva"

    @patch("process_incident.core.nodes.lookup_owner.load_inventory")
    def test_lookup_owner_sistema_desconhecido_retorna_etir(
        self, mock_load_inventory, sample_inventory
    ):
        """Sistema não mapeado deve retornar o fallback 'Desconhecido' (ETIR)."""
        from process_incident.core.nodes.lookup_owner import lookup_owner

        mock_load_inventory.return_value = sample_inventory

        state = {"incident": {
            "id": "INC-UNK-001",
            "timestamp": "2026-03-10T07:42:00Z",
            "free_text": "Sistema desconhecido com comportamento estranho.",
            "affected_systems": "sistema_inexistente_xpto",
        }}

        result = lookup_owner(state)

        assert "ETIR" in result["incident"]["responsible_person"]

    @patch("process_incident.core.nodes.lookup_owner.load_inventory")
    def test_lookup_owner_nao_usa_llm(self, mock_load_inventory, base_state, sample_inventory):
        """O nó não deve fazer nenhuma chamada a LLM."""
        import process_incident.core.nodes.lookup_owner as lookup_module
        from process_incident.core.nodes.lookup_owner import lookup_owner

        mock_load_inventory.return_value = sample_inventory

        # CORREÇÃO: em vez de tentar patchear call_llm (que não existe no módulo,
        # o que já prova que o nó não usa LLM), verificamos diretamente que o
        # atributo não está presente e que o nó executa sem erros.
        assert not hasattr(lookup_module, "call_llm"), (
            "lookup_owner não deve importar call_llm — o nó deve ser puramente determinístico"
        )

        result = lookup_owner(base_state)
        assert result is not None

    @patch("process_incident.core.nodes.lookup_owner.load_inventory")
    def test_lookup_owner_preserva_campos_existentes(
        self, mock_load_inventory, base_state, sample_inventory
    ):
        """Campos pré-existentes no incident não devem ser apagados."""
        from process_incident.core.nodes.lookup_owner import lookup_owner

        mock_load_inventory.return_value = sample_inventory

        result = lookup_owner(base_state)

        assert result["incident"]["id"] == "INC-TEST-001"
        assert result["incident"]["category"] == "Phishing"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. NÓ: recommend_containment
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecommendContainmentNode:
    """Testa o nó `recommend_containment` que recomenda passos de contenção."""

    @patch("process_incident.core.nodes.recommend_containment._load_playbook", return_value="playbook_mock")
    @patch("process_incident.core.nodes.recommend_containment.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.recommend_containment.call_llm")
    def test_recommend_containment_retorna_steps(
        self, mock_call_llm, mock_load_prompt, mock_playbook, base_state
    ):
        """O nó deve retornar containment_steps como lista."""
        from process_incident.core.nodes.recommend_containment import recommend_containment

        mock_call_llm.return_value = {
            "containment_steps": [
                "Não clicar em links suspeitos.",
                "Reportar ao ETIR.",
            ],
            "containment_justification": "Passos padrão para phishing.",
        }

        result = recommend_containment(base_state)

        assert "incident" in result
        assert isinstance(result["incident"]["containment_steps"], list)
        assert len(result["incident"]["containment_steps"]) == 2

    @patch("process_incident.core.nodes.recommend_containment._load_playbook", return_value="playbook_mock")
    @patch("process_incident.core.nodes.recommend_containment.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.recommend_containment.call_llm")
    def test_recommend_containment_retorna_justificativa(
        self, mock_call_llm, mock_load_prompt, mock_playbook, base_state
    ):
        """O nó deve retornar containment_justification como string."""
        from process_incident.core.nodes.recommend_containment import recommend_containment

        mock_call_llm.return_value = {
            "containment_steps": ["Isolar sistema."],
            "containment_justification": "Incidente de phishing requer contenção rápida.",
        }

        result = recommend_containment(base_state)

        assert isinstance(result["incident"]["containment_justification"], str)
        assert len(result["incident"]["containment_justification"]) > 0

    @patch("process_incident.core.nodes.recommend_containment._load_playbook", return_value="playbook_mock")
    @patch("process_incident.core.nodes.recommend_containment.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.recommend_containment.call_llm")
    def test_recommend_containment_llm_vazio_usa_defaults(
        self, mock_call_llm, mock_load_prompt, mock_playbook, base_state
    ):
        """Quando o LLM retorna {} deve usar listas/strings vazias como default."""
        from process_incident.core.nodes.recommend_containment import recommend_containment

        mock_call_llm.return_value = {}

        result = recommend_containment(base_state)

        assert result["incident"]["containment_steps"] == []
        assert result["incident"]["containment_justification"] == ""

    @patch("process_incident.core.nodes.recommend_containment._load_playbook", return_value="playbook_mock")
    @patch("process_incident.core.nodes.recommend_containment.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.recommend_containment.call_llm")
    def test_recommend_containment_passa_categoria_e_criticidade_ao_llm(
        self, mock_call_llm, mock_load_prompt, mock_playbook, base_state_critical
    ):
        """O user_prompt deve conter a categoria e criticidade do incidente."""
        from process_incident.core.nodes.recommend_containment import recommend_containment

        mock_call_llm.return_value = {
            "containment_steps": ["Isolar imediatamente."],
            "containment_justification": "Crítico.",
        }

        recommend_containment(base_state_critical)

        user_prompt = mock_call_llm.call_args.kwargs["user_prompt"]
        assert "True" in user_prompt  # critical=True
        assert "Institucional" in user_prompt  # scope


# ═══════════════════════════════════════════════════════════════════════════════
# 5. NÓ: draft_alert
# ═══════════════════════════════════════════════════════════════════════════════

class TestDraftAlertNode:
    """Testa o nó `draft_alert` que gera o e-mail de alerta."""

    @patch("process_incident.core.nodes.draft_alert.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.draft_alert.call_llm")
    def test_draft_alert_retorna_alert_draft(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O nó deve retornar 'incident' com 'alert_draft' preenchido."""
        from process_incident.core.nodes.draft_alert import draft_alert

        mock_call_llm.return_value = {
            "alert_draft": "Prezado João Silva, detectamos um incidente de phishing..."
        }

        result = draft_alert(base_state)

        assert "incident" in result
        assert "alert_draft" in result["incident"]
        assert "João Silva" in result["incident"]["alert_draft"]

    @patch("process_incident.core.nodes.draft_alert.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.draft_alert.call_llm")
    def test_draft_alert_llm_vazio_retorna_string_vazia(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} o alert_draft deve ser string vazia."""
        from process_incident.core.nodes.draft_alert import draft_alert

        mock_call_llm.return_value = {}

        result = draft_alert(base_state)

        assert result["incident"]["alert_draft"] == ""

    @patch("process_incident.core.nodes.draft_alert.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.draft_alert.call_llm")
    def test_draft_alert_passa_free_text_ao_llm(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O free_text original do incidente deve estar no user_prompt enviado ao LLM."""
        from process_incident.core.nodes.draft_alert import draft_alert

        mock_call_llm.return_value = {"alert_draft": "Alerta gerado."}

        draft_alert(base_state)

        user_prompt = mock_call_llm.call_args.kwargs["user_prompt"]
        assert "Passaporte UFMS" in user_prompt

    @patch("process_incident.core.nodes.draft_alert.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.draft_alert.call_llm")
    def test_draft_alert_passa_responsavel_ao_llm(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O nome do responsável deve estar presente no user_prompt."""
        from process_incident.core.nodes.draft_alert import draft_alert

        mock_call_llm.return_value = {"alert_draft": "Alerta."}

        draft_alert(base_state)

        user_prompt = mock_call_llm.call_args.kwargs["user_prompt"]
        assert "João Silva" in user_prompt

    @patch("process_incident.core.nodes.draft_alert.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.draft_alert.call_llm")
    def test_draft_alert_preserva_campos_existentes(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos pré-existentes no incident devem ser preservados."""
        from process_incident.core.nodes.draft_alert import draft_alert

        mock_call_llm.return_value = {"alert_draft": "Alerta gerado."}

        result = draft_alert(base_state)

        assert result["incident"]["id"] == "INC-TEST-001"
        assert result["incident"]["category"] == "Phishing"
        assert result["incident"]["responsible_person"] == "João Silva"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. NÓ: request_report
# ═══════════════════════════════════════════════════════════════════════════════

class TestRequestReportNode:
    """Testa o nó `request_report` que gera o template de relatório parcial."""

    @patch("process_incident.core.nodes.request_report.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.request_report.call_llm")
    def test_request_report_retorna_report_template(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O nó deve retornar 'incident' com 'report_template' preenchido."""
        from process_incident.core.nodes.request_report import request_report

        mock_call_llm.return_value = {
            "report_template": "# Relatório Parcial de Incidente\n## 1. Identificação\n..."
        }

        result = request_report(base_state)

        assert "incident" in result
        assert "report_template" in result["incident"]
        assert len(result["incident"]["report_template"]) > 0

    @patch("process_incident.core.nodes.request_report.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.request_report.call_llm")
    def test_request_report_llm_vazio_retorna_string_vazia(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Quando o LLM retorna {} o report_template deve ser string vazia."""
        from process_incident.core.nodes.request_report import request_report

        mock_call_llm.return_value = {}

        result = request_report(base_state)

        assert result["incident"]["report_template"] == ""

    @patch("process_incident.core.nodes.request_report.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.request_report.call_llm")
    def test_request_report_passa_incident_id_ao_llm(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """O incident_id deve estar presente no user_prompt enviado ao LLM."""
        from process_incident.core.nodes.request_report import request_report

        mock_call_llm.return_value = {"report_template": "Template gerado."}

        request_report(base_state)

        user_prompt = mock_call_llm.call_args.kwargs["user_prompt"]
        assert "INC-TEST-001" in user_prompt

    @patch("process_incident.core.nodes.request_report.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.request_report.call_llm")
    def test_request_report_inclui_containment_steps_no_prompt(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Os passos de contenção devem estar formatados como checklist no prompt."""
        from process_incident.core.nodes.request_report import request_report

        mock_call_llm.return_value = {"report_template": "Template."}

        request_report(base_state)

        user_prompt = mock_call_llm.call_args.kwargs["user_prompt"]
        assert "[ ]" in user_prompt

    @patch("process_incident.core.nodes.request_report.load_prompt", return_value="prompt_mock")
    @patch("process_incident.core.nodes.request_report.call_llm")
    def test_request_report_preserva_campos_existentes(
        self, mock_call_llm, mock_load_prompt, base_state
    ):
        """Campos pré-existentes no incident devem ser preservados."""
        from process_incident.core.nodes.request_report import request_report

        mock_call_llm.return_value = {"report_template": "Template."}

        result = request_report(base_state)

        assert result["incident"]["id"] == "INC-TEST-001"
        assert result["incident"]["alert_draft"] is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 7. NÓ: emit_incident
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmitIncidentNode:
    """Testa o nó `emit_incident` que persiste o resultado em JSON e CSV."""

    def _make_emit_state(self, valid_incident):
        """Estado mínimo necessário para o nó emit_incident funcionar."""
        return {"incident": valid_incident}

    @patch("process_incident.core.nodes.emit_incident.open", new_callable=mock_open)
    @patch("process_incident.core.nodes.emit_incident.os.makedirs")
    @patch("process_incident.core.nodes.emit_incident.REPORT_CSV")
    @patch("process_incident.core.nodes.emit_incident.RESPONSES_PATH")
    def test_emit_incident_retorna_incident_com_id(
        self, mock_path, mock_csv, mock_makedirs, mock_file, valid_incident
    ):
        """O incident retornado deve conter o id correto."""
        from process_incident.core.nodes.emit_incident import emit_incident

        mock_path.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_incident)

        with patch("process_incident.core.nodes.emit_incident.csv.DictWriter") as mock_writer_cls:
            mock_writer_cls.return_value = MagicMock()
            result = emit_incident(state)

        assert result["incident"]["id"] == "INC-TEST-001"

    @patch("process_incident.core.nodes.emit_incident.open", new_callable=mock_open)
    @patch("process_incident.core.nodes.emit_incident.os.makedirs")
    @patch("process_incident.core.nodes.emit_incident.REPORT_CSV")
    @patch("process_incident.core.nodes.emit_incident.RESPONSES_PATH")
    def test_emit_incident_retorna_campos_obrigatorios(
        self, mock_path, mock_csv, mock_makedirs, mock_file, valid_incident
    ):
        """O incident retornado deve conter todos os campos esperados no output."""
        from process_incident.core.nodes.emit_incident import emit_incident

        mock_path.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_incident)

        with patch("process_incident.core.nodes.emit_incident.csv.DictWriter") as mock_writer_cls:
            mock_writer_cls.return_value = MagicMock()
            result = emit_incident(state)

        expected_keys = {
            "id", "category", "category_justification",
            "critical", "critical_justification",
            "scope", "affected_systems",
            "responsible_person", "contact_info",
            "containment_steps", "containment_justification",
            "alert_draft", "report_template",
        }
        for key in expected_keys:
            assert key in result["incident"], f"Chave '{key}' ausente no incident"

    @patch("process_incident.core.nodes.emit_incident.open", new_callable=mock_open)
    @patch("process_incident.core.nodes.emit_incident.os.makedirs")
    @patch("process_incident.core.nodes.emit_incident.REPORT_CSV")
    @patch("process_incident.core.nodes.emit_incident.RESPONSES_PATH")
    def test_emit_incident_chama_makedirs(
        self, mock_path, mock_csv, mock_makedirs, mock_file, valid_incident
    ):
        """O nó deve garantir que o diretório de respostas exista."""
        from process_incident.core.nodes.emit_incident import emit_incident

        mock_path.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False

        state = self._make_emit_state(valid_incident)

        with patch("process_incident.core.nodes.emit_incident.csv.DictWriter") as mock_writer_cls:
            mock_writer_cls.return_value = MagicMock()
            emit_incident(state)

        mock_makedirs.assert_called_once()

    @patch("process_incident.core.nodes.emit_incident.open", new_callable=mock_open)
    @patch("process_incident.core.nodes.emit_incident.os.makedirs")
    @patch("process_incident.core.nodes.emit_incident.REPORT_CSV")
    @patch("process_incident.core.nodes.emit_incident.RESPONSES_PATH")
    def test_emit_incident_escreve_cabecalho_csv_quando_arquivo_novo(
        self, mock_path, mock_csv, mock_makedirs, mock_file, valid_incident
    ):
        """Quando o CSV não existe, o cabeçalho deve ser escrito."""
        from process_incident.core.nodes.emit_incident import emit_incident

        mock_path.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = False  # arquivo não existe

        state = self._make_emit_state(valid_incident)

        with patch("process_incident.core.nodes.emit_incident.csv.DictWriter") as mock_writer_cls:
            mock_writer = MagicMock()
            mock_writer_cls.return_value = mock_writer
            emit_incident(state)

        mock_writer.writeheader.assert_called_once()

    @patch("process_incident.core.nodes.emit_incident.open", new_callable=mock_open)
    @patch("process_incident.core.nodes.emit_incident.os.makedirs")
    @patch("process_incident.core.nodes.emit_incident.REPORT_CSV")
    @patch("process_incident.core.nodes.emit_incident.RESPONSES_PATH")
    def test_emit_incident_nao_escreve_cabecalho_csv_quando_arquivo_existe(
        self, mock_path, mock_csv, mock_makedirs, mock_file, valid_incident
    ):
        """Quando o CSV já existe, o cabeçalho NÃO deve ser reescrito."""
        from process_incident.core.nodes.emit_incident import emit_incident

        mock_path.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_csv.is_file.return_value = True  # arquivo já existe

        state = self._make_emit_state(valid_incident)

        with patch("process_incident.core.nodes.emit_incident.csv.DictWriter") as mock_writer_cls:
            mock_writer = MagicMock()
            mock_writer_cls.return_value = mock_writer
            emit_incident(state)

        mock_writer.writeheader.assert_not_called()