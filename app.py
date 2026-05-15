import time
from pathlib import Path

import pandas as pd
import streamlit as st

from core.graph_builder import graph
from utilities.config import DATA_PATH
from utilities.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

LOG_FILE = Path("logs/execucao.log")

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(DATA_PATH)
    return data.to_dict(orient="records")

tickets = load_data()

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Triagem AGETIC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo minimalista extra para remover espaços em branco desnecessários do topo
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .stTextArea textarea { font-size: 15px !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# BARRA LATERAL: TERMINAL DE LOGS
# =========================================================
def get_logs():
    if not LOG_FILE.exists():
        return "Aguardando execução..."
    logs = LOG_FILE.read_text(encoding="utf-8").splitlines()
    logs.reverse() # Mostra os mais recentes no topo
    return "\n".join(logs[:50]) # Limita a 50 linhas para não pesar

with st.sidebar:
    st.markdown("### :material/terminal: Terminal de Execução")
    st.caption("Logs do sistema em tempo real")
    st.code(get_logs(), language="bash")

# =========================================================
# CABEÇALHO DO DASHBOARD
# =========================================================
st.markdown("# :material/support_agent: Central de Triagem AGETIC")
st.markdown("Plataforma automatizada de análise e roteamento operada por **LangGraph**.")
st.divider()

# =========================================================
# SEÇÃO 1: ENTRADA DE DADOS
# =========================================================
st.subheader(":material/input: Dados do Chamado")

# Recriando o mapeamento para mostrar ID + Descrição (como você pediu)
def format_ticket_label(t):
    texto = t.get("free_text", "")
    # Pega os primeiros 80 caracteres para preview
    preview = texto[:80] + "..." if len(texto) > 80 else texto
    return f"{t['id']} | {preview}"

ticket_options = {format_ticket_label(t): t for t in tickets}

with st.container(border=True):
    col_sel, col_tog = st.columns([4, 1], vertical_alignment="center")
    
    with col_sel:
        selected_label = st.selectbox(
            "Selecione um chamado do banco de dados:",
            list(ticket_options.keys()),
            label_visibility="collapsed" # Esconde o label para ficar mais limpo
        )
        
    with col_tog:
        usar_ticket_real = st.toggle("Usar dados do dataset", value=True)

    selected_ticket = ticket_options[selected_label]
    
    texto_chamado = st.text_area(
        "Descrição do Problema:",
        value=selected_ticket["free_text"] if usar_ticket_real else "",
        height=120,
        placeholder="Digite o relato do usuário aqui..."
    )

# =========================================================
# SEÇÃO 2: AÇÃO
# =========================================================
st.write("") # Respiro visual
processar = st.button("Executar Triagem Inteligente", type="primary", use_container_width=True, icon=":material/play_arrow:")

if processar:
    if not texto_chamado.strip():
        st.warning("O texto do chamado não pode estar vazio.", icon=":material/warning:")
        st.stop()

    try:
        logger.info("Processamento iniciado via Interface Web")
        ticket_payload = selected_ticket if usar_ticket_real else {
            "id": "TKT-MANUAL-001",
            "timestamp": datetime.now().isoformat(),
            "channel": "Web",
            "requester_profile": "Usuário",
            "free_text": texto_chamado
        }

        # Feedback de carregamento em formato de status
        with st.status("Analisando chamado no pipeline...", expanded=True) as status:
            st.write("Executando nós de ingestão...")
            response = graph.invoke({"ticket": ticket_payload})
            time.sleep(0.5) # Leve pausa para UX
            st.write("Calculando matriz de prioridade...")
            status.update(label="Análise concluída com sucesso!", state="complete", expanded=False)

        # Extração de resultados
        resultado = response.get("response", {})
        prioridade = resultado.get("resulting_priority", "N/A")
        urgencia = resultado.get("urgency", "N/A")
        impacto = resultado.get("impact", "N/A")
        categoria = resultado.get("category", "N/A")
        justificativa = resultado.get("priority_justification", "Sem justificativa")
        resposta_gerada = resultado.get("response_draft", "Sem resposta")

        st.divider()
        
        # =========================================================
        # SEÇÃO 3: DASHBOARD DE RESULTADOS
        # =========================================================
        st.subheader(":material/analytics: Resultado da Análise")
        
        # Banner de Alerta Dinâmico
        if prioridade == 4:
            st.error("**ALERTA CRÍTICO:** Este chamado requer intervenção imediata.", icon=":material/emergency:")
        elif prioridade == 3:
            st.warning("**ATENÇÃO:** Chamado classificado com Prioridade Alta.", icon=":material/warning:")
        else:
            st.success("Chamado processado. Prioridade controlada.", icon=":material/check_circle:")

        # Grid de Métricas (Cartões)
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
        
        # Painéis de Detalhamento
        col_det1, col_det2 = st.columns(2, gap="large")
        
        with col_det1:
            st.markdown("##### :material/gavel: Justificativa da IA")
            with st.container(border=True):
                st.info(justificativa, icon=":material/info:")
                
        with col_det2:
            st.markdown("##### :material/mail: Rascunho de Resposta")
            with st.container(border=True):
                st.success(resposta_gerada, icon=":material/mark_email_read:")

        # Payload Técnico (escondido para os jurados mais técnicos)
        with st.expander(":material/data_object: Visualizar Estado Completo (JSON)"):
            st.json(resultado)

    except Exception as e:
        logger.exception(f"Erro na interface: {e}")
        st.error(f"Falha na execução: {str(e)}", icon=":material/error:")