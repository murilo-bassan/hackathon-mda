import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# OBRIGATÓRIO SER A PRIMEIRA CHAMADA STREAMLIT
st.set_page_config(layout="wide", page_title="Triagem Geral")

from general_process.core.graph_builder import build_graph
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

graph = build_graph()

# =========================================================
# CONFIGURAÇÃO DE CAMINHOS
# =========================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT_DIR / "general_process" / "artifacts" / "logs" / "execucao.log"
GENERAL_DATA_PATH = ROOT_DIR / "general_process" / "data" / "shuffled_data.json"

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(GENERAL_DATA_PATH)
    # Garante que 'critical' seja bool nativo Python (pandas pode ler como float/int)
    if "critical" in data.columns:
        data["critical"] = data["critical"].apply(
            lambda x: None if (x is None or (isinstance(x, float) and str(x) == 'nan')) else bool(x)
        )
    return data.to_dict(orient="records")

if not GENERAL_DATA_PATH.exists():
    st.error(
        f"Arquivo de dados não encontrado: `{GENERAL_DATA_PATH}`\n\n"
        "Certifique-se de que o `shuffled_data.json` foi gerado em `general_process/data/`.",
        icon=":material/error:"
    )
    st.stop()

tickets_geral = load_data()

# =========================================================
# FUNÇÕES DE APOIO AOS LOGS
# =========================================================
def get_logs():
    if not LOG_FILE.exists():
        return f"Aguardando execução...\n\n[DEBUG] Procurando log em:\n{LOG_FILE.absolute()}"
    logs = LOG_FILE.read_text(encoding="utf-8").splitlines()
    logs.reverse()
    return "\n".join(logs)

def get_ticket_logs(ticket_id):
    if not LOG_FILE.exists():
        return "Arquivo de log não encontrado."
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if ticket_id in line]
    if not filtered:
        return f"Nenhum log registrado para {ticket_id} no arquivo atual."
    return "\n".join(filtered)

def limpar_logs():
    if LOG_FILE.exists():
        LOG_FILE.write_text("", encoding="utf-8")
    st.rerun()

def is_incident(ticket_id: str) -> bool:
    return str(ticket_id).startswith("INC")

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
st.markdown("# :material/shuffle: Triagem Geral — Chamados Misturados")
st.markdown("Processa chamados de **qualquer tipo** (requests e incidentes), classificando-os automaticamente pelo **grafo geral LangGraph**.")
st.divider()

# Navegação Principal por Abas
aba1, aba2 = st.tabs([
    "Análise de Chamado Único",
    "Teste de Estresse (Lote Aleatório)",
])

# =========================================================
# ABA 1: ANÁLISE INDIVIDUAL
# =========================================================
with aba1:
    st.subheader(":material/input: Dados do Chamado")

    def format_label(t):
        texto = t.get("free_text", "")
        preview = texto[:80] + "..." if len(texto) > 80 else texto
        tipo = "🔴 INC" if is_incident(t["id"]) else "🔵 TKT"
        return f"{tipo} | {t['id']} | {preview}"

    ticket_options = {format_label(t): t for t in tickets_geral}

    if "gen_last_selected" not in st.session_state:
        st.session_state.gen_last_selected = None

    with st.container(border=True):
        col_sel, col_tog = st.columns([4, 1], vertical_alignment="center")

        with col_sel:
            selected_label = st.selectbox(
                "Selecione um chamado do banco de dados:",
                list(ticket_options.keys()),
                label_visibility="collapsed",
                key="gen_select"
            )

        with col_tog:
            usar_ticket_real = st.toggle("Usar dados do dataset", value=True, key="toggle_general")

        selected_ticket = ticket_options[selected_label]

        if st.session_state.gen_last_selected != selected_label:
            st.session_state.gen_last_selected = selected_label
            if usar_ticket_real:
                st.session_state.gen_textarea = selected_ticket["free_text"]

        texto_chamado = st.text_area(
            "Descrição do Chamado:",
            height=120,
            placeholder="Digite o relato aqui...",
            key="gen_textarea"
        )

    st.write("")

    if "gen_executando" not in st.session_state:
        st.session_state.gen_executando = False

    if not st.session_state.gen_executando:
        processar = st.button(
            "Executar Triagem Inteligente",
            type="primary",
            use_container_width=True,
            icon=":material/play_arrow:",
            key="gen_processar"
        )
        if processar:
            st.session_state.gen_executando = True
            st.rerun()
    else:
        col_exec, col_canc = st.columns(2)
        with col_exec:
            st.button("⏳ Classificando e analisando...", disabled=True, use_container_width=True)
        with col_canc:
            if st.button("❌ Cancelar análise", use_container_width=True):
                st.session_state.gen_executando = False
                st.warning("Processamento interrompido pelo usuário.")
                st.rerun()

    if st.session_state.gen_executando:
        if not texto_chamado.strip():
            st.warning("O texto do chamado não pode estar vazio.", icon=":material/warning:")
            st.session_state.gen_executando = False
            st.stop()

        try:
            logger.info(f"Triagem geral iniciada via Interface Web para ID: {selected_ticket.get('id', 'MANUAL')}")

            ticket_payload = selected_ticket if usar_ticket_real else {
                "id": "GEN-MANUAL-001",
                "timestamp": datetime.now().isoformat(),
                "free_text": texto_chamado
            }

            # O grafo geral sempre recebe {"raw_input": ticket} -- ele mesmo decide a rota
            state_input = {"raw_input": ticket_payload}

            with st.status("Analisando chamado no pipeline geral...", expanded=True) as status:
                st.write("Classificando tipo de entrada (request / incident)...")
                response = graph.invoke(state_input)
                time.sleep(0.5)
                st.write("Roteando para subgraph correspondente...")
                status.update(label="Análise concluída com sucesso!", state="complete", expanded=False)

            st.session_state.gen_executando = False

            input_type = response.get("input_type", "indefinido")
            # grafo geral retorna 'result' com o state completo do subgrafo executado
            _result = response.get("result") or {}
            resultado_req = _result.get("response") or {}
            resultado_inc = _result.get("incident") or {}
            eh_incidente = (input_type == "incident")

            st.divider()
            st.subheader(":material/analytics: Resultado da Análise")
            st.info(f"**Rota detectada pelo grafo:** `{input_type}`", icon=":material/category:")

            # ---- RESULTADO: REQUEST ----
            if resultado_req:
                prioridade = resultado_req.get("resulting_priority", "N/A")
                urgencia = resultado_req.get("urgency", "N/A")
                impacto = resultado_req.get("impact", "N/A")
                categoria = resultado_req.get("category", "N/A")
                justificativa = resultado_req.get("priority_justification", "Sem justificativa")
                resposta_gerada = resultado_req.get("response_draft", "Sem resposta")

                if prioridade in (4, 5):
                    st.error("**ALERTA CRÍTICO:** Este chamado requer intervenção imediata.", icon=":material/emergency:")
                elif prioridade == 3:
                    st.warning("**ATENÇÃO:** Chamado classificado com Prioridade Alta.", icon=":material/warning:")
                else:
                    st.success("Chamado processado. Prioridade controlada.", icon=":material/check_circle:")

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Prioridade Final", f"Nível {prioridade}")
                with col_m2:
                    st.metric("Urgência", urgencia)
                with col_m3:
                    st.metric("Impacto", impacto)
                with col_m4:
                    st.metric("Categoria", categoria)

                st.write("")
                col_det1, col_det2 = st.columns(2, gap="large")

                with col_det1:
                    st.markdown("##### :material/gavel: Justificativa da IA")
                    with st.container(border=True):
                        st.info(justificativa, icon=":material/info:")

                with col_det2:
                    st.markdown("##### :material/mail: Rascunho de Resposta")
                    with st.container(border=True):
                        st.success(resposta_gerada, icon=":material/mark_email_read:")

                with st.expander(":material/data_object: Visualizar Estado Completo (JSON)"):
                    st.json(resultado_req)

            # ---- RESULTADO: INCIDENT ----
            elif resultado_inc:
                categoria = resultado_inc.get("category", "N/A")
                critico = resultado_inc.get("critical", False)
                justificativa_cat = resultado_inc.get("category_justification", "Sem justificativa")
                escopo = resultado_inc.get("scope", "N/A")
                sistemas = resultado_inc.get("affected_systems", "N/A")
                responsavel = resultado_inc.get("responsible_person", "N/A")
                contato = resultado_inc.get("contact_info", "N/A")
                passos = resultado_inc.get("containment_steps", [])
                justificativa_cont = resultado_inc.get("containment_justification", "")
                alerta = resultado_inc.get("alert_draft", "Sem alerta gerado")
                relatorio = resultado_inc.get("report_template", "")

                if critico:
                    st.error("**INCIDENTE CRÍTICO:** Requer resposta e contenção imediata.", icon=":material/emergency:")
                else:
                    st.warning("**INCIDENTE REGISTRADO:** Severidade controlada.", icon=":material/warning:")

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Categoria", categoria)
                with col_m2:
                    st.metric("Criticidade", "🔴 Crítico" if critico else "🟡 Normal")
                with col_m3:
                    st.metric("Escopo", escopo)

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
                    st.json(resultado_inc)

            else:
                st.warning("Não foi possível identificar o tipo de chamado ou o JSON retornou vazio.")
                with st.expander(":material/data_object: Resposta Completa do Grafo (JSON)"):
                    st.json(response)

        except Exception as e:
            logger.exception(f"Erro na triagem geral individual: {e}")
            st.session_state.gen_executando = False
            st.error(f"Falha na execução: {str(e)}", icon=":material/error:")


# =========================================================
# ABA 2: TESTE EM LOTE (ESTRESSE/BATCH)
# =========================================================
with aba2:
    st.subheader(":material/dynamic_feed: Teste de Estresse (Amostragem Mista)")
    st.write(
        "Sorteie chamados misturados (requests e incidentes) e veja o grafo geral classificar e processar cada um, "
        "exibindo os resultados em **duas planilhas separadas** por tipo."
    )

    if "gen_resultados_req" not in st.session_state:
        st.session_state.gen_resultados_req = []
    if "gen_resultados_inc" not in st.session_state:
        st.session_state.gen_resultados_inc = []
    if "gen_qte_lote" not in st.session_state:
        st.session_state.gen_qte_lote = 0
    if "gen_executando_lote" not in st.session_state:
        st.session_state.gen_executando_lote = False
    if "gen_lote_tickets" not in st.session_state:
        st.session_state.gen_lote_tickets = []
    if "gen_lote_index" not in st.session_state:
        st.session_state.gen_lote_index = 0

    qte_lote = st.slider(
        "Quantidade de chamados para o teste:",
        min_value=1, max_value=30, value=5, step=1,
        key="gen_slider"
    )

    if not st.session_state.gen_executando_lote:
        if st.button(
            "Iniciar Processamento em Lote",
            icon=":material/bolt:",
            use_container_width=True,
            type="secondary",
            key="gen_btn_start"
        ):
            st.session_state.gen_qte_lote = qte_lote
            st.session_state.gen_resultados_req = []
            st.session_state.gen_resultados_inc = []
            # Garante pelo menos 40% de incidentes; o resto vem do shuffle geral
            _incidents = [t for t in tickets_geral if is_incident(t["id"])]
            _n_inc_min = max(1, round(qte_lote * 0.4))
            _n_inc_min = min(_n_inc_min, len(_incidents))
            _inc_fixos = random.sample(_incidents, _n_inc_min)
            _restantes = [t for t in tickets_geral if t not in _inc_fixos]
            _complemento = random.sample(_restantes, qte_lote - _n_inc_min)
            _lote = _inc_fixos + _complemento
            random.shuffle(_lote)
            st.session_state.gen_lote_tickets = _lote
            st.session_state.gen_lote_index = 0
            st.session_state.gen_executando_lote = True
            st.rerun()
    else:
        col_btn_load, col_btn_cancel = st.columns([3, 1])
        with col_btn_load:
            st.button(
                f"⏳ Processando chamado {st.session_state.gen_lote_index + 1} de {st.session_state.gen_qte_lote}...",
                disabled=True,
                use_container_width=True,
                key="gen_btn_progress"
            )
        with col_btn_cancel:
            if st.button("Cancelar", type="primary", use_container_width=True, icon=":material/close:", key="gen_btn_cancel"):
                st.session_state.gen_executando_lote = False
                st.session_state.gen_lote_tickets = []
                st.session_state.gen_lote_index = 0
                st.warning("Processamento em lote interrompido pelo usuário.")
                st.rerun()

    # ---- EXECUÇÃO PASSO A PASSO ----
    if st.session_state.gen_executando_lote:
        idx = st.session_state.gen_lote_index
        total = st.session_state.gen_qte_lote
        lote_sorteado = st.session_state.gen_lote_tickets

        if idx < total:
            ticket_real = lote_sorteado[idx]
            
            # O grafo geral sempre recebe {"raw_input": ticket}
            state_input = {"raw_input": ticket_real}

            with st.spinner(f"Agente analisando ID: {ticket_real['id']}..."):
                try:
                    logger.info(f"Lote geral: Analisando {ticket_real['id']}")
                    resp = graph.invoke(state_input)

                    # Avaliamos o gabarito original para saber em qual planilha o chamado DEVERIA estar
                    eh_inc_real = is_incident(ticket_real["id"])

                    # ---- REGISTRO: REQUEST ----
                    if not eh_inc_real:
                        _result_lote = resp.get("result") or {}
                        llm_data = _result_lote.get("response") or {}

                        cat_real = str(ticket_real.get("category") or "none").strip().lower()
                        cat_ia = str(llm_data.get("category") or "none").strip().lower()
                        cat_ok = (cat_real == cat_ia)

                        dept_real = str(ticket_real.get("department") or "none").strip().lower()
                        dept_ia = str(llm_data.get("department") or "none").strip().lower()
                        dept_ok = (dept_real in dept_ia) or (dept_ia in dept_real)

                        def norm_prio(val):
                            if val is None or str(val).strip().lower() in ["none", "nan", ""]: return 0
                            try: return int(float(val))
                            except: return 0

                        prio_real_norm = norm_prio(ticket_real.get("resulting_priority"))
                        prio_ia_norm = norm_prio(llm_data.get("resulting_priority"))

                        def avaliar_prio(real, ia):
                            if real == 0 and ia == 0: return "Acerto (Draft)", "draft_ok"
                            if real == 0 and ia != 0: return "Erro (Ignorou Draft)", "draft_err"
                            if real != 0 and ia == 0: return "Erro (Falso Draft)", "draft_err"
                            diff = abs(real - ia)
                            if diff == 0: return "Acerto Exato", True
                            if diff == 1: return "Acerto Técnico", True
                            if diff in [2, 3]: return "Erro Técnico", False
                            return "Erro Crítico", False

                        status_prio_texto, prio_ok = avaliar_prio(prio_real_norm, prio_ia_norm)

                        if prio_ok == "draft_ok" and cat_ok and dept_ok:
                            status_str = "✅ Sucesso"
                        elif prio_ok == "draft_ok":
                            status_str = "⚠️ Divergência"
                        elif prio_ok == "draft_err":
                            status_str = "🚨 Erro de Draft"
                        elif cat_ok and (prio_ok is True) and dept_ok:
                            status_str = "✅ Sucesso"
                        elif (prio_ok is False) and "Erro Crítico" in status_prio_texto:
                            status_str = "🚨 Falha Crítica"
                        else:
                            status_str = "⚠️ Divergência"

                        st.session_state.gen_resultados_req.append({
                            "ID": ticket_real["id"],
                            "Resumo (Input)": ticket_real["free_text"],
                            "Cat. Real": ticket_real.get("category"),
                            "Cat. IA": llm_data.get("category"),
                            "Prio. Real": prio_real_norm if prio_real_norm != 0 else "Draft",
                            "Prio. IA": prio_ia_norm if prio_ia_norm != 0 else "Draft",
                            "Status Prio": status_prio_texto,
                            "Setor Real": ticket_real.get("department"),
                            "Setor IA": llm_data.get("department"),
                            "Status": status_str,
                            "cat_ok": cat_ok,
                            "prio_ok": prio_ok,
                            "dept_ok": dept_ok,
                            "ticket_original": ticket_real,
                            "resposta_llm": llm_data
                        })

                    # ---- REGISTRO: INCIDENT ----
                    else:
                        _result_lote_inc = resp.get("result") or {}
                        llm_data = _result_lote_inc.get("incident") or {}

                        cat_real = str(ticket_real.get("category") or "none").strip().lower()
                        cat_ia = str(llm_data.get("category") or "none").strip().lower()
                        cat_ok = (cat_real == cat_ia)

                        # pandas pode converter bool para int (1/0) ou string — normaliza aqui
                        _crit_raw = ticket_real.get("critical")
                        if _crit_raw is None or (isinstance(_crit_raw, float) and str(_crit_raw) == 'nan'):
                            crit_real = None
                        else:
                            crit_real = bool(_crit_raw)
                        crit_ia = llm_data.get("critical")
                        if crit_ia is not None:
                            crit_ia = bool(crit_ia)
                        if crit_real is None:
                            crit_ok = "Ignorado"
                        else:
                            crit_ok = (crit_real == crit_ia)

                        status_str = "✅ Sucesso" if (cat_ok and (crit_ok is True or crit_ok == "Ignorado")) else "⚠️ Divergência"

                        st.session_state.gen_resultados_inc.append({
                            "ID": ticket_real["id"],
                            "Resumo (Input)": ticket_real["free_text"],
                            "Cat. Real": ticket_real.get("category"),
                            "Cat. IA": llm_data.get("category"),
                            "Crítico Real": "Sim" if crit_real is True else ("N/A" if crit_real is None else "Não"),
                            "Crítico IA": "Sim" if crit_ia else "Não",
                            "Responsável IA": llm_data.get("responsible_person", "N/A"),
                            "Status": status_str,
                            "cat_ok": cat_ok,
                            "crit_ok": crit_ok,
                            "incident_original": ticket_real,
                            "resposta_llm": llm_data
                        })

                except Exception as e:
                    logger.error(f"Erro no lote geral. Ticket {ticket_real['id']}: {e}")

            st.session_state.gen_lote_index += 1
            st.rerun()
        else:
            st.session_state.gen_executando_lote = False
            st.rerun()

    # =========================================================
    # EXIBIÇÃO DOS RESULTADOS: DUAS PLANILHAS SEPARADAS
    # =========================================================
    resultados_req = st.session_state.gen_resultados_req
    resultados_inc = st.session_state.gen_resultados_inc

    if resultados_req or resultados_inc:
        st.divider()
        st.markdown("#### Resultado da Amostragem Atual")

        total_processados = len(resultados_req) + len(resultados_inc)
        col_sum1, col_sum2, col_sum3 = st.columns(3)
        col_sum1.metric("Total Processados", total_processados)
        col_sum2.metric("🔵 Requests", len(resultados_req))
        col_sum3.metric("🔴 Incidentes", len(resultados_inc))

        def colorir_status(val):
            if val == "⚠️ Divergência": return 'background-color: #5c1818; color: #ffb8b8'
            elif val == "✅ Sucesso": return 'background-color: #0f5132; color: #d1e7dd'
            elif val in ["🚨 Falha Crítica", "🚨 Erro de Draft"]: return 'background-color: #8b0000; color: #ffffff'
            return ''

        # ---- PLANILHA 1: REQUESTS ----
        st.write("")
        st.markdown("### 🔵 Requests")

        if resultados_req:
            total_req = len(resultados_req)
            hits_cat_r = sum(1 for r in resultados_req if r["cat_ok"])
            hits_dept_r = sum(1 for r in resultados_req if r["dept_ok"])
            testes_prio_r = sum(1 for r in resultados_req if r["prio_ok"] in [True, False])
            hits_prio_r = sum(1 for r in resultados_req if r["prio_ok"] is True)

            col_r1, col_r2, col_r3 = st.columns(3)
            with st.container(border=True):
                col_r1.metric("Acertos (Categoria)", f"{(hits_cat_r/total_req)*100:.0f}%", f"{hits_cat_r}/{total_req}")
            with st.container(border=True):
                if testes_prio_r > 0:
                    col_r2.metric("Acertos (Prioridade) *S/ Drafts", f"{(hits_prio_r/testes_prio_r)*100:.0f}%", f"{hits_prio_r}/{testes_prio_r}")
                else:
                    col_r2.metric("Acertos (Prioridade)", "N/A", "0/0")
            with st.container(border=True):
                col_r3.metric("Acertos (Departamento)", f"{(hits_dept_r/total_req)*100:.0f}%", f"{hits_dept_r}/{total_req}")

            df_req = pd.DataFrame(resultados_req)
            df_req_display = df_req.drop(columns=["cat_ok", "prio_ok", "dept_ok", "ticket_original", "resposta_llm"])

            evento_req = st.dataframe(
                df_req_display.style.map(colorir_status, subset=["Status"]),
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="gen_tabela_req",
                column_config={
                    "Resumo (Input)": st.column_config.TextColumn("Resumo (Input)", width="large")
                }
            )

            linhas_req = evento_req.selection.rows
            if linhas_req:
                st.divider()
                dados = resultados_req[linhas_req[0]]
                ticket_detalhe = dados["ticket_original"]
                llm_detalhe = dados["resposta_llm"]

                st.markdown(f"### 🔍 Inspeção Detalhada: `{ticket_detalhe['id']}`")
                with st.container(border=True):
                    st.markdown("**Relato do Usuário:**")
                    st.write(ticket_detalhe["free_text"])

                st.write("")
                col_det_m1, col_det_m2, col_det_m3, col_det_m4 = st.columns(4)
                prio_ia_det = llm_detalhe.get("resulting_priority", 0)
                with col_det_m1:
                    st.metric("Prioridade IA", f"Nível {prio_ia_det}" if prio_ia_det != 0 else "0 (Draft)")
                with col_det_m2:
                    st.metric("Urgência IA", llm_detalhe.get("urgency", "N/A"))
                with col_det_m3:
                    st.metric("Impacto IA", llm_detalhe.get("impact", "N/A"))
                with col_det_m4:
                    st.metric("Categoria IA", llm_detalhe.get("category", "N/A"))

                st.write("")
                col_info1, col_info2 = st.columns(2, gap="large")
                with col_info1:
                    st.markdown("##### :material/gavel: Justificativa da IA")
                    with st.container(border=True):
                        st.info(llm_detalhe.get("priority_justification", "Sem justificativa"), icon=":material/info:")
                with col_info2:
                    st.markdown("##### :material/mail: Rascunho de Resposta")
                    with st.container(border=True):
                        st.success(llm_detalhe.get("response_draft", "Sem resposta"), icon=":material/mark_email_read:")

                st.write("")
                with st.expander(":material/data_object: Visualizar Estado Completo do Ticket (JSON)"):
                    st.json(llm_detalhe)
                st.markdown(f"##### :material/terminal: Logs do Ticket `{ticket_detalhe['id']}`")
                with st.container(border=True):
                    st.code(get_ticket_logs(ticket_detalhe["id"]), language="bash")

        else:
            st.info("Nenhum request foi sorteado neste lote.", icon=":material/info:")

        # ---- PLANILHA 2: INCIDENTES ----
        st.write("")
        st.markdown("### 🔴 Incidentes")

        if resultados_inc:
            total_inc = len(resultados_inc)
            hits_cat_i = sum(1 for r in resultados_inc if r["cat_ok"])
            testes_crit_validos = sum(1 for r in resultados_inc if r["crit_ok"] in [True, False])
            hits_crit_i = sum(1 for r in resultados_inc if r["crit_ok"] is True)

            col_i1, col_i2 = st.columns(2)
            with st.container(border=True):
                col_i1.metric("Acertos (Categoria)", f"{(hits_cat_i/total_inc)*100:.0f}%", f"{hits_cat_i}/{total_inc}")
            with st.container(border=True):
                if testes_crit_validos > 0:
                    col_i2.metric("Acertos (Criticidade)", f"{(hits_crit_i/testes_crit_validos)*100:.0f}%", f"{hits_crit_i}/{testes_crit_validos}")
                else:
                    col_i2.metric("Acertos (Criticidade)", "N/A", "0/0")

            df_inc = pd.DataFrame(resultados_inc)
            df_inc_display = df_inc.drop(columns=["cat_ok", "crit_ok", "incident_original", "resposta_llm"])

            evento_inc = st.dataframe(
                df_inc_display.style.map(colorir_status, subset=["Status"]),
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="gen_tabela_inc",
                column_config={
                    "Resumo (Input)": st.column_config.TextColumn("Resumo (Input)", width="large")
                }
            )

            linhas_inc = evento_inc.selection.rows
            if linhas_inc:
                st.divider()
                dados = resultados_inc[linhas_inc[0]]
                incident_detalhe = dados["incident_original"]
                llm_detalhe = dados["resposta_llm"]

                st.markdown(f"### 🔍 Inspeção Detalhada: `{incident_detalhe['id']}`")
                with st.container(border=True):
                    st.markdown("**Relato do Usuário:**")
                    st.write(incident_detalhe["free_text"])

                st.write("")
                critico_ia = llm_detalhe.get("critical", False)
                col_det_m1, col_det_m2, col_det_m3 = st.columns(3)
                with col_det_m1:
                    st.metric("Categoria IA", llm_detalhe.get("category", "N/A"))
                with col_det_m2:
                    st.metric("Criticidade IA", "🔴 Crítico" if critico_ia else "🟡 Normal")
                with col_det_m3:
                    st.metric("Escopo IA", llm_detalhe.get("scope", "N/A"))

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
                st.markdown(f"##### :material/terminal: Logs do Incidente `{incident_detalhe['id']}`")
                with st.container(border=True):
                    st.code(get_ticket_logs(incident_detalhe["id"]), language="bash")

        else:
            st.info("Nenhum incidente foi sorteado neste lote.", icon=":material/info:")


# =========================================================
# LOGS EM TELA CHEIA (RODAPÉ)
# =========================================================
st.write("")
st.write("")
with st.expander(":material/fullscreen: Visualizar Logs em Tela Cheia (Geral)"):
    col_titulo, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("Limpar Logs", key="gen_limpar_full"):
            limpar_logs()

    with st.container(height=600):
        st.code(get_logs(), language="bash")