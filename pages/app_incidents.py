import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# OBRIGATÓRIO SER A PRIMEIRA CHAMADA STREAMLIT
st.set_page_config(layout="wide", page_title="Triagem de Incidentes")

from process_incident.core.subgraph_incident_builder import build_incident_subgraph
from process_incident.utilities.config import DATA_PATH as INCIDENT_DATA_PATH
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

# =========================================================
# CONFIGURAÇÃO DE CAMINHOS
# =========================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT_DIR / "general_process" / "artifacts" / "logs" / "execucao.log"

# Grafo dedicado a incidentes
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
        return f"Aguardando execução...\n\n[DEBUG] O sistema está procurando o log em:\n{LOG_FILE.absolute()}"
    logs = LOG_FILE.read_text(encoding="utf-8").splitlines()
    logs.reverse()
    return "\n".join(logs)

def get_incident_logs(incident_id):
    if not LOG_FILE.exists():
        return "Arquivo de log não encontrado."
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    inc_lines = [line for line in lines if incident_id in line]
    if not inc_lines:
        return f"Nenhum log registrado para o incidente {incident_id} no arquivo atual."
    return "\n".join(inc_lines)

def limpar_logs():
    if LOG_FILE.exists():
        LOG_FILE.write_text("", encoding="utf-8")
    st.rerun()

# =========================================================
# BARRA LATERAL: TERMINAL DE LOGS GLOBAL
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

    if "inc_last_selected" not in st.session_state:
        st.session_state.inc_last_selected = None

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

        if st.session_state.inc_last_selected != selected_label:
            st.session_state.inc_last_selected = selected_label
            if usar_ticket_real:
                st.session_state.inc_textarea = selected_incident["free_text"]

        texto_chamado = st.text_area(
            "Descrição do Incidente:",
            height=120,
            placeholder="Descreva o incidente reportado aqui...",
            key="inc_textarea"
        )

    st.write("")

    if "inc_executando" not in st.session_state:
        st.session_state.inc_executando = False

    if not st.session_state.inc_executando:
        processar = st.button(
            "Executar Triagem de Incidente",
            type="primary",
            use_container_width=True,
            icon=":material/play_arrow:",
            key="inc_processar"
        )
        if processar:
            st.session_state.inc_executando = True
            st.rerun()
    else:
        col_exec, col_canc = st.columns(2)
        with col_exec:
            st.button("⏳ Analisando incidente...", disabled=True, use_container_width=True)
        with col_canc:
            if st.button("❌ Cancelar análise", use_container_width=True):
                st.session_state.inc_executando = False
                st.warning("Processamento interrompido pelo usuário.")
                st.rerun()

    if st.session_state.inc_executando:
        if not texto_chamado.strip():
            st.warning("O texto do incidente não pode estar vazio.", icon=":material/warning:")
            st.session_state.inc_executando = False
            st.stop()

        try:
            logger.info(f"Processamento de incidente individual iniciado via Interface Web para ID: {selected_incident.get('id', 'MANUAL')}")

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

            st.session_state.inc_executando = False

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

            if usar_ticket_real:
                st.markdown("#### 🎯 Validação vs Dataset Original")
                
                real_cat = selected_incident.get("category", "N/A")
                real_crit = selected_incident.get("critical")
                
                if str(real_cat).strip().lower() == str(categoria).strip().lower():
                    st.success(f"**Categoria:** Acerto ({categoria})")
                else:
                    st.error(f"**Categoria:** Divergência (IA: {categoria} | Real: {real_cat})")

                if real_crit is None:
                    st.info("**Criticidade:** Ignorada (Não há definição de criticidade no dataset original para este incidente).")
                elif bool(real_crit) == bool(critico):
                    st.success(f"**Criticidade:** Acerto ({'Crítico' if critico else 'Normal'})")
                else:
                    st.error(f"**Criticidade:** Erro (IA classificou como {'Crítico' if critico else 'Normal'} | Esperado: {'Crítico' if real_crit else 'Normal'})")

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
            st.session_state.inc_executando = False
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
                    logger.info(f"Processamento em lote: Analisando incidente {incident_real['id']}")
                    resp = incident_graph.invoke({"incident": incident_real})
                    llm_data = resp.get("incident", {})

                    cat_real = str(incident_real.get("category") or "none").strip().lower()
                    cat_ia = str(llm_data.get("category") or "none").strip().lower()
                    cat_ok = (cat_real == cat_ia)

                    crit_real = incident_real.get("critical")
                    crit_ia = llm_data.get("critical")
                    
                    if crit_real is None:
                        crit_ok = "Ignorado"
                    else:
                        crit_ok = (bool(crit_real) == bool(crit_ia))

                    status_str = "✅ Sucesso" if (cat_ok and (crit_ok is True or crit_ok == "Ignorado")) else "⚠️ Divergência"

                    st.session_state.inc_resultados_lote.append({
                        "ID": incident_real["id"],
                        "Resumo (Input)": incident_real["free_text"],
                        "Cat. Real": incident_real.get("category"),
                        "Cat. IA": llm_data.get("category"),
                        "Crítico Real": "Sim" if crit_real else ("N/A" if crit_real is None else "Não"),
                        "Crítico IA": "Sim" if crit_ia else "Não",
                        "Responsável IA": llm_data.get("responsible_person", "N/A"),
                        "Status": status_str,
                        "cat_ok": cat_ok,
                        "crit_ok": crit_ok,
                        "incident_original": incident_real,
                        "resposta_llm": llm_data
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
        total_lote = len(lote_atual)

        hits_cat = sum(1 for r in lote_atual if r["cat_ok"])
        
        testes_crit_validos = sum(1 for r in lote_atual if r["crit_ok"] in [True, False])
        hits_crit = sum(1 for r in lote_atual if r["crit_ok"] is True)

        col_L1, col_L2 = st.columns(2)
        with st.container(border=True):
            col_L1.metric("Acertos (Categoria)", f"{(hits_cat/total_lote)*100:.0f}%", f"{hits_cat}/{total_lote}")
        with st.container(border=True):
            if testes_crit_validos > 0:
                col_L2.metric("Acertos (Criticidade)", f"{(hits_crit/testes_crit_validos)*100:.0f}%", f"{hits_crit}/{testes_crit_validos}")
            else:
                col_L2.metric("Acertos (Criticidade)", "N/A", "0/0")

        df_lote = pd.DataFrame(lote_atual)
        df_display = df_lote.drop(columns=["cat_ok", "crit_ok", "incident_original", "resposta_llm"])

        def colorir_status(val):
            if val == "⚠️ Divergência": return 'background-color: #5c1818; color: #ffb8b8'
            elif val == "✅ Sucesso": return 'background-color: #0f5132; color: #d1e7dd'
            return ''

        evento_tabela = st.dataframe(
            df_display.style.map(colorir_status, subset=['Status']),
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            column_config={
                "Resumo (Input)": st.column_config.TextColumn("Resumo (Input)", width="large")
            }
        )

        # =========================================================
        # VISÃO DETALHADA + JSON + LOGS DO INCIDENTE SELECIONADO
        # =========================================================
        linhas_selecionadas = evento_tabela.selection.rows
        
        if linhas_selecionadas:
            st.divider()
            idx_selecionado = linhas_selecionadas[0]
            dados_linha = lote_atual[idx_selecionado]
            
            incident_detalhe = dados_linha["incident_original"]
            llm_detalhe = dados_linha["resposta_llm"]
            
            st.markdown(f"### 🔍 Inspeção Detalhada: `{incident_detalhe['id']}`")
            
            with st.container(border=True):
                st.markdown("**Relato do Usuário:**")
                st.write(incident_detalhe['free_text'])
                
            st.write("")
            
            critico_ia = llm_detalhe.get('critical', False)
            
            col_det_m1, col_det_m2, col_det_m3 = st.columns(3)
            with col_det_m1:
                st.metric(label="Categoria IA", value=llm_detalhe.get('category', 'N/A'))
            with col_det_m2:
                st.metric(label="Criticidade IA", value="🔴 Crítico" if critico_ia else "🟡 Normal")
            with col_det_m3:
                st.metric(label="Escopo IA", value=llm_detalhe.get('scope', 'N/A'))

            st.write("")
            col_info1, col_info2 = st.columns(2, gap="large")

            with col_info1:
                st.markdown("##### :material/gavel: Justificativa da Categoria")
                with st.container(border=True):
                    st.info(llm_detalhe.get("category_justification", "Sem justificativa"), icon=":material/info:")

                st.markdown("##### :material/computer: Sistemas Afetados")
                with st.container(border=True):
                    st.warning(llm_detalhe.get("affected_systems", "Não identificados"), icon=":material/dns:")

                st.markdown("##### :material/person: Responsável")
                with st.container(border=True):
                    st.write(f"**{llm_detalhe.get('responsible_person', 'N/A')}**")
                    st.caption(llm_detalhe.get("contact_info", "N/A"))

            with col_info2:
                st.markdown("##### :material/shield: Passos de Contenção")
                with st.container(border=True):
                    passos_ia = llm_detalhe.get("containment_steps", [])
                    if passos_ia:
                        for i, passo in enumerate(passos_ia, 1):
                            st.write(f"{i}. {passo}")
                        just_cont = llm_detalhe.get("containment_justification", "")
                        if just_cont:
                            st.caption(f"_Justificativa: {just_cont}_")
                    else:
                        st.write("Nenhum passo de contenção definido.")

                st.markdown("##### :material/notifications_active: Rascunho de Alerta")
                with st.container(border=True):
                    st.error(llm_detalhe.get("alert_draft", "Sem alerta gerado"), icon=":material/campaign:")

            relatorio_ia = llm_detalhe.get("report_template", "")
            if relatorio_ia:
                with st.expander(":material/description: Ver Template de Relatório Gerado"):
                    st.text(relatorio_ia)

            st.write("")
            with st.expander(":material/data_object: Visualizar Estado Completo do Incidente (JSON)"):
                st.json(llm_detalhe)
                
            st.write("")
            st.markdown(f"##### :material/terminal: Histórico de Logs do Incidente `{incident_detalhe['id']}`")
            with st.container(border=True):
                st.code(get_incident_logs(incident_detalhe['id']), language="bash")


# =========================================================
# LOGS EM TELA CHEIA (RODAPÉ)
# =========================================================
st.write("")
st.write("")
with st.expander(":material/fullscreen: Visualizar Logs em Tela Cheia (Geral)"):
    col_titulo, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("Limpar Logs", key="inc_limpar_full"):
            limpar_logs()

    with st.container(height=600):
        st.code(get_logs(), language="bash")