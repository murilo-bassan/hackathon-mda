from concurrent.futures import ThreadPoolExecutor, Future
from core.state.state import State
from utilities.utils import call_llm
from utilities.config import (
    SCORE_URGENCY_PROMPT_PATH,
    SCORE_IMPACT_PROMPT_PATH,
    JUSTIFY_PRIORITY_PROMPT_PATH
)
from utilities.prompt_loader import load_prompt
from utilities.logger_config import setup_logger

logger = setup_logger(__name__)

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_SCORE = 2          # valor conservador quando o LLM falha
FAILSAFE_PRIORITY = PRIORITY_MAX # em caso de erro, escala para humano

def _calculate_priority(urgency: int, impact: int) -> int:
    """
    Calcula a prioridade resultante de forma determinística.
    Usa o valor máximo entre urgência e impacto como base, ponderando
    a média aritmética para amenizar extremos isolados.
    Resultado sempre dentro do intervalo [PRIORITY_MIN, PRIORITY_MAX].
    """
    raw = (max(urgency, impact) + round((urgency + impact) / 2)) / 2
    return max(PRIORITY_MIN, min(PRIORITY_MAX, round(raw)))

def _build_justification_prompt_input(
    ticket_text: str,
    urgency: int,
    impact: int,
    resulting_priority: int,
) -> str:
    """Monta o user_prompt para o nó de justificativa de forma legível e rastreável."""
    return (
        f"Ticket: {ticket_text}\n\n"
        f"Urgency: {urgency}\n"
        f"Impact: {impact}\n"
        f"Resulting priority: {resulting_priority}"
    )

def score_priority(state: State) -> dict:
    """
    Nó LangGraph responsável por calcular a prioridade do chamado.
 
    Fluxo:
      1. Urgência e Impacto são avaliados pelo LLM em paralelo.
      2. A prioridade resultante é calculada deterministicamente em Python.
      3. Uma justificativa textual é gerada pelo LLM com base nos três valores.
 
    Em caso de falha do LLM em qualquer etapa, o nó registra o erro,
    marca `llm_error` no estado e eleva a prioridade ao máximo como
    medida de segurança (fail-safe para fila humana).
    """
    ticket      = state.get("ticket", {})
    ticket_id   = ticket.get("id", "UNKNOWN")
    ticket_text = ticket.get("free_text", "")
    partial     = dict(state.get("response", {}))
 
    # ── Etapa 1: urgência e impacto em paralelo ────────────────────────────────
 
    urgency_prompt = load_prompt(SCORE_URGENCY_PROMPT_PATH)
    impact_prompt  = load_prompt(SCORE_IMPACT_PROMPT_PATH)
 
    logger.info(f"[{ticket_id}] Calculando urgência e impacto em paralelo")
 
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_urgency: Future = executor.submit(
            call_llm, urgency_prompt, f"Ticket: {ticket_text}"
        )
        future_impact: Future = executor.submit(
            call_llm, impact_prompt, f"Ticket: {ticket_text}"
        )
        urgency_response = future_urgency.result()
        impact_response  = future_impact.result()
 
    # Detecta falha silenciosa do call_llm (retorna {} em caso de erro)
    urgency_failed = not urgency_response or "urgency" not in urgency_response
    impact_failed  = not impact_response  or "impact"  not in impact_response
 
    if urgency_failed or impact_failed:
        failed_fields = [f for f, failed in [("urgency", urgency_failed), ("impact", impact_failed)] if failed]
        logger.error(f"[{ticket_id}] Falha do LLM nos campos: {failed_fields}. Aplicando fail-safe.")
 
        partial.update({
            "urgency":              DEFAULT_SCORE,
            "impact":               DEFAULT_SCORE,
            "resulting_priority":   FAILSAFE_PRIORITY,
            "priority_justification": (
                "Erro interno na avaliação automática. "
                "Chamado escalado para analista humano por segurança."
            ),
            "llm_error": f"score_priority falhou nos campos: {failed_fields}",
        })
        return {"response": partial}
 
    urgency = int(urgency_response["urgency"])
    impact  = int(impact_response["impact"])
 
    logger.info(f"[{ticket_id}] Urgência={urgency} | Impacto={impact}")
 
    # ── Etapa 2: cálculo determinístico da prioridade ──────────────────────────
 
    resulting_priority = _calculate_priority(urgency, impact)
 
    logger.info(f"[{ticket_id}] Prioridade resultante={resulting_priority}")
 
    # ── Etapa 3: justificativa (depende dos valores acima — não paralelizável) ──
 
    justification_prompt = load_prompt(JUSTIFY_PRIORITY_PROMPT_PATH)
    justification_input  = _build_justification_prompt_input(
        ticket_text, urgency, impact, resulting_priority
    )
 
    justification_response = call_llm(justification_prompt, justification_input)
 
    if not justification_response or "priority_justification" not in justification_response:
        logger.warning(f"[{ticket_id}] LLM não retornou justificativa. Usando fallback textual.")
 
    priority_justification = justification_response.get(
        "priority_justification",
        f"Urgência {urgency} e Impacto {impact} resultaram em prioridade {resulting_priority}.",
    )
 
    # ── Atualiza estado ────────────────────────────────────────────────────────
 
    partial.update({
        "urgency":               urgency,
        "impact":                impact,
        "resulting_priority":    resulting_priority,
        "priority_justification": priority_justification,
    })
 
    return {"response": partial}