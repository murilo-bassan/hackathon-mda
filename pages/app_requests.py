import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# OBRIGATÓRIO SER A PRIMEIRA CHAMADA STREAMLIT
st.set_page_config(layout="wide", page_title="Triagem de Requests")

from process_request.core.subgraph_request_builder import build_request_subgraph
from process_request.utilities.config import DATA_PATH as REQUEST_DATA_PATH
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

# =========================================================
# CONFIGURAÇÃO DE CAMINHOS
# =========================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT_DIR / "general_process" / "artifacts" / "logs" / "execucao.log"

# Grafo dedicado a requests
request_graph = build_request_subgraph()

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(REQUEST_DATA_PATH)
    return data.to_dict(orient="records")

tickets = load_data()

# =========================================================
# FUNÇÕES DE APOIO AOS LOGS
# =========================================================
def get_logs():
    if not LOG_FILE.exists():
        return f"Aguardando execução...\n\n[DEBUG] O sistema está procurando o log em:\n{LOG_FILE.absolute()}"
    logs = LOG_FILE.read_text(encoding="utf-8").splitlines()
    logs.reverse()
    return "\n".join(logs)

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
st.markdown("# :material/support_agent: Triagem de Requests")
st.markdown("Plataforma automatizada de análise e roteamento de **chamados de request** operada por **LangGraph**.")
st.divider()

# Navegação Principal por Abas
aba1, aba2 = st.tabs([
    "Análise de Chamado Único",
    "Teste de Estresse (Lote Aleatório)"
])

# =========================================================
# ABA 1: ANÁLISE INDIVIDUAL
# =========================================================
with aba1:
    st.subheader(":material/input: Dados do Chamado")

    def format_ticket_label(t):
        texto = t.get("free_text", "")
        preview = texto[:80] + "..." if len(texto) > 80 else texto
        return f"{t['id']} | {preview}"

    ticket_options = {format_ticket_label(t): t for t in tickets}

    if "req_last_selected" not in st.session_state:
        st.session_state.req_last_selected = None

    with st.container(border=True):
        col_sel, col_tog = st.columns([4, 1], vertical_alignment="center")

        with col_sel:
            selected_label = st.selectbox(
                "Selecione um chamado do banco de dados:",
                list(ticket_options.keys()),
                label_visibility="collapsed",
                key="req_select"
            )

        with col_tog:
            usar_ticket_real = st.toggle("Usar dados do dataset", value=True, key="toggle_request")

        selected_ticket = ticket_options[selected_label]

        if st.session_state.req_last_selected != selected_label:
            st.session_state.req_last_selected = selected_label
            if usar_ticket_real:
                st.session_state.req_textarea = selected_ticket["free_text"]

        texto_chamado = st.text_area(
            "Descrição do Problema:",
            height=120,
            placeholder="Digite o relato do usuário aqui...",
            key="req_textarea"
        )

    st.write("")

    if "req_executando" not in st.session_state:
        st.session_state.req_executando = False

    if not st.session_state.req_executando:
        processar = st.button(
            "Executar Triagem Inteligente",
            type="primary",
            use_container_width=True,
            icon=":material/play_arrow:",
            key="req_processar"
        )
        if processar:
            st.session_state.req_executando = True
            st.rerun()
    else:
        col_exec, col_canc = st.columns(2)
        with col_exec:
            st.button("⏳ Executando prompt...", disabled=True, use_container_width=True)
        with col_canc:
            if st.button("❌ Cancelar prompt", use_container_width=True):
                st.session_state.req_executando = False
                st.warning("Processamento interrompido pelo usuário.")
                st.rerun()

    if st.session_state.req_executando:
        if not texto_chamado.strip():
            st.warning("O texto do chamado não pode estar vazio.", icon=":material/warning:")
            st.session_state.req_executando = False
            st.stop()

        try:
            logger.info(f"Processamento de request individual iniciado via Interface Web para ID: {selected_ticket.get('id', 'MANUAL')}")
            ticket_payload = selected_ticket if usar_ticket_real else {
                "id": "TKT-MANUAL-001",
                "timestamp": datetime.now().isoformat(),
                "channel": "Web",
                "requester_profile": "Usuário",
                "free_text": texto_chamado
            }

            with st.status("Analisando chamado no pipeline...", expanded=True) as status:
                st.write("Executando nós de ingestão...")
                response = request_graph.invoke({"ticket": ticket_payload})
                time.sleep(0.5)
                st.write("Calculando matriz de prioridade...")
                status.update(label="Análise concluída com sucesso!", state="complete", expanded=False)

            st.session_state.req_executando = False

            resultado = response.get("response", {})
            prioridade = resultado.get("resulting_priority", "N/A")
            urgencia = resultado.get("urgency", "N/A")
            impacto = resultado.get("impact", "N/A")
            categoria = resultado.get("category", "N/A")
            justificativa = resultado.get("priority_justification", "Sem justificativa")
            resposta_gerada = resultado.get("response_draft", "Sem resposta")

            st.divider()
            st.subheader(":material/analytics: Resultado da Análise")

            if prioridade == 4 or prioridade == 5:
                st.error("**ALERTA CRÍTICO:** Este chamado requer intervenção imediata.", icon=":material/emergency:")
            elif prioridade == 3:
                st.warning("**ATENÇÃO:** Chamado classificado com Prioridade Alta.", icon=":material/warning:")
            else:
                st.success("Chamado processado. Prioridade controlada.", icon=":material/check_circle:")

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric(label="Prioridade Final", value=f"Nível {prioridade}" if prioridade != 0 else "0 (Draft)")
            with col_m2:
                st.metric(label="Urgência", value=urgencia)
            with col_m3:
                st.metric(label="Impacto", value=impacto)
            with col_m4:
                st.metric(label="Categoria", value=categoria)

            st.write("")

            # VALIDAÇÃO INDIVIDUAL VS DATASET
            if usar_ticket_real:
                st.markdown("#### 🎯 Validação vs Dataset Original")
                
                def normalizar_prioridade_ind(val):
                    if val is None or str(val).strip().lower() in ["none", "nan", ""]: return 0
                    try: return int(float(val))
                    except: return 0

                real_cat = selected_ticket.get("category", "N/A")
                real_prio = normalizar_prioridade_ind(selected_ticket.get("resulting_priority"))
                ia_prio = normalizar_prioridade_ind(prioridade)
                
                if str(real_cat).strip().lower() == str(categoria).strip().lower():
                    st.success(f"**Categoria:** Acerto ({categoria})")
                else:
                    st.error(f"**Categoria:** Divergência (IA: {categoria} | Real: {real_cat})")

                if real_prio == 0 and ia_prio == 0:
                    st.success("**Prioridade/Draft:** Acerto (O ticket foi corretamente classificado como Draft/Incompleto).")
                elif real_prio == 0 and ia_prio != 0:
                    st.error(f"**Prioridade/Draft:** Erro (Era esperado um Draft, mas a IA atribuiu Nível {ia_prio}).")
                elif real_prio != 0 and ia_prio == 0:
                    st.error(f"**Prioridade/Draft:** Erro (O ticket tinha Nível {real_prio}, mas a IA desviou para Draft incorretamente).")
                else:
                    diff = abs(real_prio - ia_prio)
                    if diff == 0:
                        st.success(f"**Prioridade:** Acerto Exato (Nível {ia_prio})")
                    elif diff == 1:
                        st.success(f"**Prioridade:** Acerto Técnico (IA: {ia_prio} | Real: {real_prio}) - Dentro da margem de tolerância.")
                    elif diff in [2, 3]:
                        st.warning(f"**Prioridade:** Erro Técnico (IA: {ia_prio} | Real: {real_prio}) - Diferença de {diff} pontos.")
                    else:
                        st.error(f"**Prioridade:** Erro Crítico (IA: {ia_prio} | Real: {real_prio}) - Diferença gritante.")
            
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
                st.json(resultado)

        except Exception as e:
            st.session_state.req_executando = False
            logger.exception(f"Erro na interface de request individual: {e}")
            st.error(f"Falha na execução: {str(e)}", icon=":material/error:")


# =========================================================
# ABA 2: TESTE EM LOTE (ESTRESSE/BATCH)
# =========================================================
with aba2:
    st.subheader(":material/dynamic_feed: Teste de Estresse (Amostragem)")
    st.write("Sorteie chamados do dataset e veja a IA processar em lote, comparando os resultados com o gabarito original em tempo real.")

    if "req_resultados_lote" not in st.session_state:
        st.session_state.req_resultados_lote = []
    if "req_qte_lote" not in st.session_state:
        st.session_state.req_qte_lote = 0
    if "req_executando_lote" not in st.session_state:
        st.session_state.req_executando_lote = False
    if "req_lote_tickets" not in st.session_state:
        st.session_state.req_lote_tickets = []
    if "req_lote_index" not in st.session_state:
        st.session_state.req_lote_index = 0

    qte_lote = st.slider("Quantidade de chamados para o teste:", min_value=1, max_value=30, value=5, step=1, key="req_slider")

    if not st.session_state.req_executando_lote:
        if st.button("Iniciar Processamento em Lote", icon=":material/bolt:", use_container_width=True, type="secondary", key="req_btn_start"):
            st.session_state.req_qte_lote = qte_lote
            st.session_state.req_resultados_lote = []
            st.session_state.req_lote_tickets = random.sample(tickets, qte_lote)
            st.session_state.req_lote_index = 0
            st.session_state.req_executando_lote = True
            st.rerun()
    else:
        col_btn_load, col_btn_cancel = st.columns([3, 1])
        with col_btn_load:
            st.button(
                f"⏳ Processando chamado {st.session_state.req_lote_index + 1} de {st.session_state.req_qte_lote}...",
                disabled=True,
                use_container_width=True,
                key="req_btn_progress"
            )
        with col_btn_cancel:
            if st.button("Cancelar Solicitação", type="primary", use_container_width=True, icon=":material/close:", key="req_btn_cancel"):
                st.session_state.req_executando_lote = False
                st.session_state.req_lote_tickets = []
                st.session_state.req_lote_index = 0
                st.warning("Processamento em lote interrompido pelo usuário.")
                st.rerun()

    if st.session_state.req_executando_lote:
        idx = st.session_state.req_lote_index
        total = st.session_state.req_qte_lote
        lote_sorteado = st.session_state.req_lote_tickets

        if idx < total:
            ticket_real = lote_sorteado[idx]

            with st.spinner(f"Agente analisando ID: {ticket_real['id']}..."):
                try:
                    logger.info(f"Processamento em lote: Analisando ticket {ticket_real['id']}")
                    resp = request_graph.invoke({"ticket": ticket_real})
                    llm_data = resp.get("response", {})

                    cat_real = str(ticket_real.get("category") or "none").strip().lower()
                    cat_ia = str(llm_data.get("category") or "none").strip().lower()
                    cat_ok = (cat_real == cat_ia)

                    dept_real = str(ticket_real.get("department") or "none").strip().lower()
                    dept_ia = str(llm_data.get("department") or "none").strip().lower()
                    dept_ok = (dept_real in dept_ia) or (dept_ia in dept_real)

                    def normalizar_prioridade_lote(val):
                        if val is None or str(val).strip().lower() in ["none", "nan", ""]: return 0
                        try: return int(float(val))
                        except: return 0

                    prio_real_norm = normalizar_prioridade_lote(ticket_real.get("resulting_priority"))
                    prio_ia_norm = normalizar_prioridade_lote(llm_data.get("resulting_priority"))

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

                    st.session_state.req_resultados_lote.append({
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

                except Exception as e:
                    logger.error(f"Erro no lote de request. Ticket {ticket_real['id']}: {e}")

            st.session_state.req_lote_index += 1
            st.rerun()
        else:
            st.session_state.req_executando_lote = False
            st.rerun()

    if st.session_state.req_resultados_lote:
        st.divider()
        st.markdown("#### Resultado da Amostragem Atual")

        lote_atual = st.session_state.req_resultados_lote
        total_lote = len(lote_atual)

        hits_cat = sum(1 for r in lote_atual if r["cat_ok"])
        hits_dept = sum(1 for r in lote_atual if r["dept_ok"])
        
        testes_prio_validos = sum(1 for r in lote_atual if r["prio_ok"] in [True, False])
        hits_prio = sum(1 for r in lote_atual if r["prio_ok"] is True)

        col_L1, col_L2, col_L3 = st.columns(3)
        with st.container(border=True):
            col_L1.metric("Acertos (Categoria)", f"{(hits_cat/total_lote)*100:.0f}%", f"{hits_cat}/{total_lote}")
        with st.container(border=True):
            if testes_prio_validos > 0:
                col_L2.metric("Acertos (Prioridade) *S/ Drafts", f"{(hits_prio/testes_prio_validos)*100:.0f}%", f"{hits_prio}/{testes_prio_validos}")
            else:
                col_L2.metric("Acertos (Prioridade)", "N/A", "0/0")
        with st.container(border=True):
            col_L3.metric("Acertos (Departamento)", f"{(hits_dept/total_lote)*100:.0f}%", f"{hits_dept}/{total_lote}")

        df_lote = pd.DataFrame(lote_atual)
        df_display = df_lote.drop(columns=["cat_ok", "prio_ok", "dept_ok", "ticket_original", "resposta_llm"])

        def colorir_status(val):
            if val == "⚠️ Divergência": return 'background-color: #5c1818; color: #ffb8b8'
            elif val == "✅ Sucesso": return 'background-color: #0f5132; color: #d1e7dd'
            elif val in ["🚨 Falha Crítica", "🚨 Erro de Draft"]: return 'background-color: #8b0000; color: #ffffff'
            return ''

        # Caixa de seleção nativa integrada ao rerun
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
        # VISÃO DETALHADA + JSON DO ITEM SELECIONADO
        # =========================================================
        linhas_selecionadas = evento_tabela.selection.rows
        
        if linhas_selecionadas:
            st.divider()
            idx_selecionado = linhas_selecionadas[0]
            dados_linha = lote_atual[idx_selecionado]
            
            ticket_detalhe = dados_linha["ticket_original"]
            llm_detalhe = dados_linha["resposta_llm"]
            
            st.markdown(f"### 🔍 Inspeção Detalhada: `{ticket_detalhe['id']}`")
            
            with st.container(border=True):
                st.markdown("**Relato do Usuário:**")
                st.write(ticket_detalhe['free_text'])
                
            st.write("")
            
            col_det_m1, col_det_m2, col_det_m3, col_det_m4 = st.columns(4)
            with col_det_m1:
                prio_ia_detalhe = llm_detalhe.get('resulting_priority', 0)
                st.metric("Prioridade IA", f"Nível {prio_ia_detalhe}" if prio_ia_detalhe != 0 else "0 (Draft)")
            with col_det_m2:
                st.metric("Urgência IA", llm_detalhe.get('urgency', 'N/A'))
            with col_det_m3:
                st.metric("Impacto IA", llm_detalhe.get('impact', 'N/A'))
            with col_det_m4:
                st.metric("Categoria IA", llm_detalhe.get('category', 'N/A'))

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

            # EXPANDER COM O ESTADO DO JSON DO TICKETS EM LOTE
            st.write("")
            with st.expander(":material/data_object: Visualizar Estado Completo do Ticket (JSON)"):
                st.json(llm_detalhe)

# =========================================================
# LOGS EM TELA CHEIA (RODAPÉ)
# =========================================================
st.write("")
st.write("")
with st.expander(":material/fullscreen: Visualizar Logs em Tela Cheia (Geral)"):
    col_titulo, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("Limpar Logs", key="req_limpar_full"):
            limpar_logs()

    with st.container(height=600):
        st.code(get_logs(), language="bash")