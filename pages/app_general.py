import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from general_process.core.graph_builder import graph
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

LOG_FILE = Path("logs/execucao.log")

# Caminho dos dados gerais (misturados: requests + incidents)
GENERAL_DATA_PATH = Path("general_process/data/shuffled_data.json")

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(GENERAL_DATA_PATH)
    return data.to_dict(orient="records")

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
st.markdown("# :material/shuffle: Triagem Geral — Chamados Misturados")
st.markdown("Processa chamados de **qualquer tipo** (request ou incident), classificando-os automaticamente via **LangGraph**.")
st.divider()

# =========================================================
# CARREGAMENTO SEGURO DOS DADOS
# =========================================================
if not GENERAL_DATA_PATH.exists():
    st.error(
        f"Arquivo de dados não encontrado: `{GENERAL_DATA_PATH}`\n\n"
        "Certifique-se de que o arquivo `shuffled_data.json` foi gerado em `general_process/data/`.",
        icon=":material/error:"
    )
    st.stop()

tickets = load_data()

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

    def format_ticket_label(t):
        texto = t.get("free_text", "")
        preview = texto[:80] + "..." if len(texto) > 80 else texto
        return f"{t['id']} | {preview}"

    ticket_options = {format_ticket_label(t): t for t in tickets}

    with st.container(border=True):
        col_sel, col_tog = st.columns([4, 1], vertical_alignment="center")

        with col_sel:
            selected_label = st.selectbox(
                "Selecione um chamado do banco de dados:",
                list(ticket_options.keys()),
                label_visibility="collapsed",
                key="general_select"
            )

        with col_tog:
            usar_ticket_real = st.toggle("Usar dados do dataset", value=True, key="toggle_general")

        selected_ticket = ticket_options[selected_label]

        texto_chamado = st.text_area(
            "Descrição do Problema:",
            value=selected_ticket["free_text"] if usar_ticket_real else "",
            height=120,
            placeholder="Digite o relato do usuário aqui...",
            key="general_textarea"
        )

    st.write("")
    processar = st.button(
        "Executar Triagem Inteligente",
        type="primary",
        use_container_width=True,
        icon=":material/play_arrow:",
        key="general_processar"
    )

    if processar:
        if not texto_chamado.strip():
            st.warning("O texto do chamado não pode estar vazio.", icon=":material/warning:")
            st.stop()

        try:
            logger.info("Processamento geral individual iniciado via Interface Web")
            ticket_payload = selected_ticket if usar_ticket_real else {
                "id": "TKT-MANUAL-001",
                "timestamp": datetime.now().isoformat(),
                "channel": "Web",
                "requester_profile": "Usuário",
                "free_text": texto_chamado
            }

            with st.status("Analisando chamado no pipeline...", expanded=True) as status:
                st.write("Classificando tipo de entrada (request / incident)...")
                response = graph.invoke({"ticket": ticket_payload})
                time.sleep(0.5)
                st.write("Roteando para subgraph correspondente...")
                status.update(label="Análise concluída com sucesso!", state="complete", expanded=False)

            # O grafo geral pode retornar via "response" (request) ou via "incident" (incident)
            resultado = response.get("response") or response.get("incident") or {}
            input_type = response.get("input_type", "indefinido")

            st.divider()
            st.subheader(":material/analytics: Resultado da Análise")

            st.info(f"**Tipo detectado:** `{input_type}`", icon=":material/category:")

            # --- Exibição adaptada por tipo ---
            if input_type == "request":
                prioridade = resultado.get("resulting_priority", "N/A")
                urgencia = resultado.get("urgency", "N/A")
                impacto = resultado.get("impact", "N/A")
                categoria = resultado.get("category", "N/A")
                justificativa = resultado.get("priority_justification", "Sem justificativa")
                resposta_gerada = resultado.get("response_draft", "Sem resposta")

                if prioridade in (4, 5):
                    st.error("**ALERTA CRÍTICO:** Este chamado requer intervenção imediata.", icon=":material/emergency:")
                elif prioridade == 3:
                    st.warning("**ATENÇÃO:** Chamado classificado com Prioridade Alta.", icon=":material/warning:")
                else:
                    st.success("Chamado processado. Prioridade controlada.", icon=":material/check_circle:")

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric(label="Prioridade Final", value=f"Nível {prioridade}")
                with col_m2:
                    st.metric(label="Urgência", value=urgencia)
                with col_m3:
                    st.metric(label="Impacto", value=impacto)
                with col_m4:
                    st.metric(label="Categoria", value=categoria)

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

            elif input_type == "incident":
                categoria = resultado.get("category", "N/A")
                critico = resultado.get("critical", False)
                escopo = resultado.get("scope", "N/A")
                responsavel = resultado.get("responsible_person", "N/A")
                contato = resultado.get("contact_info", "N/A")
                passos = resultado.get("containment_steps", [])
                alerta = resultado.get("alert_draft", "Sem alerta gerado")

                if critico:
                    st.error("**INCIDENTE CRÍTICO:** Requer resposta imediata.", icon=":material/emergency:")
                else:
                    st.warning("**INCIDENTE REGISTRADO:** Severidade controlada.", icon=":material/warning:")

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric(label="Categoria", value=categoria)
                with col_m2:
                    st.metric(label="Escopo", value=escopo)
                with col_m3:
                    st.metric(label="Responsável", value=responsavel)

                st.write("")
                col_det1, col_det2 = st.columns(2, gap="large")

                with col_det1:
                    st.markdown("##### :material/person: Contato do Responsável")
                    with st.container(border=True):
                        st.info(contato or "Não identificado", icon=":material/contact_phone:")

                    st.markdown("##### :material/shield: Passos de Contenção")
                    with st.container(border=True):
                        if passos:
                            for i, passo in enumerate(passos, 1):
                                st.write(f"{i}. {passo}")
                        else:
                            st.write("Nenhum passo definido.")

                with col_det2:
                    st.markdown("##### :material/notifications_active: Rascunho de Alerta")
                    with st.container(border=True):
                        st.warning(alerta, icon=":material/campaign:")

            else:
                st.warning("Tipo de chamado não identificado. Verifique o JSON completo abaixo.")

            with st.expander(":material/data_object: Visualizar Estado Completo (JSON)"):
                st.json(response)

        except Exception as e:
            logger.exception(f"Erro na interface geral individual: {e}")
            st.error(f"Falha na execução: {str(e)}", icon=":material/error:")


# =========================================================
# ABA 2: TESTE EM LOTE
# =========================================================
with aba2:
    st.subheader(":material/dynamic_feed: Teste de Estresse (Amostragem)")
    st.write("Sorteie chamados misturados do dataset e veja a IA classificar e processar em lote em tempo real.")

    if "gen_resultados_lote" not in st.session_state:
        st.session_state.gen_resultados_lote = []
    if "gen_qte_lote" not in st.session_state:
        st.session_state.gen_qte_lote = 0
    if "gen_executando_lote" not in st.session_state:
        st.session_state.gen_executando_lote = False
    if "gen_lote_tickets" not in st.session_state:
        st.session_state.gen_lote_tickets = []
    if "gen_lote_index" not in st.session_state:
        st.session_state.gen_lote_index = 0

    qte_lote = st.slider("Quantidade de chamados para o teste:", min_value=1, max_value=30, value=5, step=1, key="gen_slider")

    if not st.session_state.gen_executando_lote:
        if st.button("Iniciar Processamento em Lote", icon=":material/bolt:", use_container_width=True, type="secondary", key="gen_btn_start"):
            st.session_state.gen_qte_lote = qte_lote
            st.session_state.gen_resultados_lote = []
            st.session_state.gen_lote_tickets = random.sample(tickets, qte_lote)
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

    if st.session_state.gen_executando_lote:
        idx = st.session_state.gen_lote_index
        total = st.session_state.gen_qte_lote
        lote_sorteado = st.session_state.gen_lote_tickets

        if idx < total:
            ticket_real = lote_sorteado[idx]

            with st.spinner(f"Agente analisando ID: {ticket_real['id']}..."):
                try:
                    resp = graph.invoke({"ticket": ticket_real})
                    input_type = resp.get("input_type", "indefinido")
                    llm_data = resp.get("response") or resp.get("incident") or {}

                    # Validações genéricas (categoria sempre presente em ambos os tipos)
                    cat_real = str(ticket_real.get("category") or "none").strip().lower()
                    cat_ia = str(llm_data.get("category") or "none").strip().lower()
                    cat_ok = (cat_real == cat_ia)

                    tipo_ok = (
                        (input_type == "request" and ticket_real["id"].startswith("TKT")) or
                        (input_type == "incident" and ticket_real["id"].startswith("INC"))
                    )

                    status_str = "✅ Sucesso" if (cat_ok and tipo_ok) else "⚠️ Divergência"

                    st.session_state.gen_resultados_lote.append({
                        "ID": ticket_real["id"],
                        "Resumo (Input)": ticket_real["free_text"][:45] + "...",
                        "Tipo Detectado": input_type,
                        "Tipo Correto?": "✅" if tipo_ok else "❌",
                        "Cat. Real": ticket_real.get("category"),
                        "Cat. IA": llm_data.get("category"),
                        "Cat. Correta?": "✅" if cat_ok else "❌",
                        "Status": status_str,
                        "cat_ok": cat_ok,
                        "tipo_ok": tipo_ok,
                    })

                except Exception as e:
                    logger.error(f"Erro no lote geral. Ticket {ticket_real['id']}: {e}")

            st.session_state.gen_lote_index += 1
            st.rerun()
        else:
            st.session_state.gen_executando_lote = False
            st.rerun()

    if st.session_state.gen_resultados_lote:
        st.divider()
        st.markdown("#### Resultado da Amostragem Atual")

        lote_atual = st.session_state.gen_resultados_lote

        hits_cat = sum(1 for r in lote_atual if r["cat_ok"])
        hits_tipo = sum(1 for r in lote_atual if r["tipo_ok"])

        col_L1, col_L2 = st.columns(2)
        with st.container(border=True):
            col_L1.metric("Acertos (Tipo de Chamado)", f"{(hits_tipo/len(lote_atual))*100:.0f}%", f"{hits_tipo}/{len(lote_atual)}")
        with st.container(border=True):
            col_L2.metric("Acertos (Categoria)", f"{(hits_cat/len(lote_atual))*100:.0f}%", f"{hits_cat}/{len(lote_atual)}")

        df_lote = pd.DataFrame(lote_atual)
        df_display = df_lote.drop(columns=["cat_ok", "tipo_ok"])

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
        if st.button("Limpar Logs", key="gen_limpar_full"):
            limpar_logs()

    with st.container(height=600):
        st.code(get_logs(), language="bash")