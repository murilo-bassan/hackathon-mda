import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from process_incident.core.subgraph_incident_builder import build_incident_subgraph
from process_incident.utilities.config import DATA_PATH as INCIDENT_DATA_PATH
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

LOG_FILE = Path("logs/execucao.log")

# Grafo dedicado a incidentes (sem passar pelo classify_input do grafo geral)
incident_graph = build_incident_subgraph()

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(INCIDENT_DATA_PATH)
    return data.to_dict(orient="records")

incidents = load_data()

# =========================================================
# FUNÇÕES DE APOIO AOS LOGS
# =========================================================
def get_logs():
    if not LOG_FILE.exists():
        return "Aguardando execução..."
    logs = LOG_FILE.read_text(encoding="utf-8").splitlines()
    logs.reverse()
    return "\n".join(logs)

def limpar_logs():
    if LOG_FILE.exists():
        LOG_FILE.write_text("", encoding="utf-8")
    st.rerun()

# =========================================================
# BARRA LATERAL: TERMINAL DE LOGS
# =========================================================
with st.sidebar:
    st.markdown("### :material/terminal: Terminal de Execução")
    st.caption("Logs do sistema em tempo real")

    if st.button("Limpar Logs", icon=":material/delete:", use_container_width=True):
        limpar_logs()

    with st.container(height=450):
        st.code(get_logs(), language="bash")

# =========================================================
# CABEÇALHO DO DASHBOARD
# =========================================================
st.markdown("# :material/warning: Triagem de Incidentes")
st.markdown("Plataforma automatizada de análise e resposta a **incidentes de segurança e operacionais** operada por **LangGraph**.")
st.divider()

# Navegação Principal por Abas
aba1, aba2 = st.tabs([
    "Análise de Incidente Único",
    "Teste de Estresse (Lote Aleatório)",
])

# =========================================================
# ABA 1: ANÁLISE INDIVIDUAL
# =========================================================
with aba1:
    st.subheader(":material/input: Dados do Incidente")

    def format_incident_label(t):
        texto = t.get("free_text", "")
        preview = texto[:80] + "..." if len(texto) > 80 else texto
        return f"{t['id']} | {preview}"

    incident_options = {format_incident_label(t): t for t in incidents}

    with st.container(border=True):
        col_sel, col_tog = st.columns([4, 1], vertical_alignment="center")

        with col_sel:
            selected_label = st.selectbox(
                "Selecione um incidente do banco de dados:",
                list(incident_options.keys()),
                label_visibility="collapsed",
                key="inc_select"
            )

        with col_tog:
            usar_ticket_real = st.toggle("Usar dados do dataset", value=True, key="toggle_incident")

        selected_incident = incident_options[selected_label]

        texto_chamado = st.text_area(
            "Descrição do Incidente:",
            value=selected_incident["free_text"] if usar_ticket_real else "",
            height=120,
            placeholder="Descreva o incidente reportado aqui...",
            key="inc_textarea"
        )

    st.write("")
    processar = st.button(
        "Executar Triagem de Incidente",
        type="primary",
        use_container_width=True,
        icon=":material/play_arrow:",
        key="inc_processar"
    )

    if processar:
        if not texto_chamado.strip():
            st.warning("O texto do incidente não pode estar vazio.", icon=":material/warning:")
            st.stop()

        try:
            logger.info("Processamento de incidente individual iniciado via Interface Web")

            incident_payload = selected_incident if usar_ticket_real else {
                "id": "INC-MANUAL-001",
                "timestamp": datetime.now().isoformat(),
                "free_text": texto_chamado
            }

            with st.status("Analisando incidente no pipeline...", expanded=True) as status:
                st.write("Executando ingestão e validação do incidente...")
                response = incident_graph.invoke({"incident": incident_payload})
                time.sleep(0.5)
                st.write("Classificando criticidade e identificando responsável...")
                status.update(label="Análise concluída com sucesso!", state="complete", expanded=False)

            resultado = response.get("incident", {})
            categoria = resultado.get("category", "N/A")
            critico = resultado.get("critical", False)
            justificativa_cat = resultado.get("category_justification", "Sem justificativa")
            justificativa_crit = resultado.get("critical_justification", "Sem justificativa")
            escopo = resultado.get("scope", "N/A")
            sistemas = resultado.get("affected_systems", "N/A")
            responsavel = resultado.get("responsible_person", "N/A")
            contato = resultado.get("contact_info", "N/A")
            passos = resultado.get("containment_steps", [])
            justificativa_cont = resultado.get("containment_justification", "")
            alerta = resultado.get("alert_draft", "Sem alerta gerado")
            relatorio = resultado.get("report_template", "")

            st.divider()
            st.subheader(":material/analytics: Resultado da Análise")

            if critico:
                st.error("**INCIDENTE CRÍTICO:** Requer resposta e contenção imediata.", icon=":material/emergency:")
            else:
                st.warning("**INCIDENTE REGISTRADO:** Severidade controlada. Seguir procedimento padrão.", icon=":material/warning:")

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric(label="Categoria", value=categoria)
            with col_m2:
                st.metric(label="Criticidade", value="🔴 Crítico" if critico else "🟡 Normal")
            with col_m3:
                st.metric(label="Escopo", value=escopo)

            st.write("")
            col_det1, col_det2 = st.columns(2, gap="large")

            with col_det1:
                st.markdown("##### :material/gavel: Justificativa da Categoria")
                with st.container(border=True):
                    st.info(justificativa_cat, icon=":material/info:")

                st.markdown("##### :material/computer: Sistemas Afetados")
                with st.container(border=True):
                    st.warning(sistemas or "Não identificados", icon=":material/dns:")

                st.markdown("##### :material/person: Responsável")
                with st.container(border=True):
                    st.write(f"**{responsavel}**")
                    st.caption(contato)

            with col_det2:
                st.markdown("##### :material/shield: Passos de Contenção")
                with st.container(border=True):
                    if passos:
                        for i, passo in enumerate(passos, 1):
                            st.write(f"{i}. {passo}")
                        if justificativa_cont:
                            st.caption(f"_Justificativa: {justificativa_cont}_")
                    else:
                        st.write("Nenhum passo de contenção definido.")

                st.markdown("##### :material/notifications_active: Rascunho de Alerta")
                with st.container(border=True):
                    st.error(alerta, icon=":material/campaign:")

            if relatorio:
                with st.expander(":material/description: Ver Template de Relatório"):
                    st.text(relatorio)

            with st.expander(":material/data_object: Visualizar Estado Completo (JSON)"):
                st.json(resultado)

        except Exception as e:
            logger.exception(f"Erro na interface de incidente individual: {e}")
            st.error(f"Falha na execução: {str(e)}", icon=":material/error:")


# =========================================================
# ABA 2: TESTE EM LOTE (ESTRESSE/BATCH)
# =========================================================
with aba2:
    st.subheader(":material/dynamic_feed: Teste de Estresse (Amostragem)")
    st.write("Sorteie incidentes do dataset e veja a IA processar em lote, comparando os resultados com o gabarito original em tempo real.")

    if "inc_resultados_lote" not in st.session_state:
        st.session_state.inc_resultados_lote = []
    if "inc_qte_lote" not in st.session_state:
        st.session_state.inc_qte_lote = 0
    if "inc_executando_lote" not in st.session_state:
        st.session_state.inc_executando_lote = False
    if "inc_lote_tickets" not in st.session_state:
        st.session_state.inc_lote_tickets = []
    if "inc_lote_index" not in st.session_state:
        st.session_state.inc_lote_index = 0

    qte_lote = st.slider("Quantidade de incidentes para o teste:", min_value=1, max_value=30, value=5, step=1, key="inc_slider")

    if not st.session_state.inc_executando_lote:
        if st.button("Iniciar Processamento em Lote", icon=":material/bolt:", use_container_width=True, type="secondary", key="inc_btn_start"):
            st.session_state.inc_qte_lote = qte_lote
            st.session_state.inc_resultados_lote = []
            st.session_state.inc_lote_tickets = random.sample(incidents, qte_lote)
            st.session_state.inc_lote_index = 0
            st.session_state.inc_executando_lote = True
            st.rerun()
    else:
        col_btn_load, col_btn_cancel = st.columns([3, 1])
        with col_btn_load:
            st.button(
                f"⏳ Processando incidente {st.session_state.inc_lote_index + 1} de {st.session_state.inc_qte_lote}...",
                disabled=True,
                use_container_width=True,
                key="inc_btn_progress"
            )
        with col_btn_cancel:
            if st.button("Cancelar Solicitação", type="primary", use_container_width=True, icon=":material/close:", key="inc_btn_cancel"):
                st.session_state.inc_executando_lote = False
                st.session_state.inc_lote_tickets = []
                st.session_state.inc_lote_index = 0
                st.warning("Processamento em lote interrompido pelo usuário.")
                st.rerun()

    if st.session_state.inc_executando_lote:
        idx = st.session_state.inc_lote_index
        total = st.session_state.inc_qte_lote
        lote_sorteado = st.session_state.inc_lote_tickets

        if idx < total:
            incident_real = lote_sorteado[idx]

            with st.spinner(f"Agente analisando ID: {incident_real['id']}..."):
                try:
                    resp = incident_graph.invoke({"incident": incident_real})
                    llm_data = resp.get("incident", {})

                    # Validação de categoria
                    cat_real = str(incident_real.get("category") or "none").strip().lower()
                    cat_ia = str(llm_data.get("category") or "none").strip().lower()
                    cat_ok = (cat_real == cat_ia)

                    # Validação de criticidade (se existir no gabarito)
                    crit_real = incident_real.get("critical")
                    crit_ia = llm_data.get("critical")
                    # Se gabarito não tem campo, considera acerto por ausência
                    crit_ok = (crit_real is None) or (bool(crit_real) == bool(crit_ia))

                    status_str = "✅ Sucesso" if (cat_ok and crit_ok) else "⚠️ Divergência"

                    st.session_state.inc_resultados_lote.append({
                        "ID": incident_real["id"],
                        "Resumo (Input)": incident_real["free_text"][:45] + "...",
                        "Cat. Real": incident_real.get("category"),
                        "Cat. IA": llm_data.get("category"),
                        "Crítico Real": "Sim" if crit_real else ("N/A" if crit_real is None else "Não"),
                        "Crítico IA": "Sim" if crit_ia else "Não",
                        "Responsável IA": llm_data.get("responsible_person", "N/A"),
                        "Status": status_str,
                        "cat_ok": cat_ok,
                        "crit_ok": crit_ok,
                    })

                except Exception as e:
                    logger.error(f"Erro no lote de incidentes. Ticket {incident_real['id']}: {e}")

            st.session_state.inc_lote_index += 1
            st.rerun()
        else:
            st.session_state.inc_executando_lote = False
            st.rerun()

    if st.session_state.inc_resultados_lote:
        st.divider()
        st.markdown("#### Resultado da Amostragem Atual")

        lote_atual = st.session_state.inc_resultados_lote

        hits_cat = sum(1 for r in lote_atual if r["cat_ok"])
        hits_crit = sum(1 for r in lote_atual if r["crit_ok"])

        col_L1, col_L2 = st.columns(2)
        with st.container(border=True):
            col_L1.metric("Acertos (Categoria)", f"{(hits_cat/len(lote_atual))*100:.0f}%", f"{hits_cat}/{len(lote_atual)}")
        with st.container(border=True):
            col_L2.metric("Acertos (Criticidade)", f"{(hits_crit/len(lote_atual))*100:.0f}%", f"{hits_crit}/{len(lote_atual)}")

        df_lote = pd.DataFrame(lote_atual)
        df_display = df_lote.drop(columns=["cat_ok", "crit_ok"])

        def colorir_status(val):
            if val == "⚠️ Divergência":
                return 'background-color: #5c1818; color: #ffb8b8'
            elif val == "✅ Sucesso":
                return 'background-color: #0f5132; color: #d1e7dd'
            return ''

        st.dataframe(
            df_display.style.map(colorir_status, subset=['Status']),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# LOGS EM TELA CHEIA (RODAPÉ)
# =========================================================
st.write("")
st.write("")
with st.expander(":material/fullscreen: Visualizar Logs em Tela Cheia"):
    col_titulo, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("Limpar Logs", key="inc_limpar_full"):
            limpar_logs()

    with st.container(height=600):
        st.code(get_logs(), language="bash")