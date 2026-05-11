from state.state import State
from utilities.utils import call_llm

def classify_type(state: State) -> dict:
    # A variável abaixo guarda todo o manual de instruções e os exemplos
    system_prompt = """
    You are a Level 1 IT triage analyst. Classify the ticket.
    Categories: "Requisição", "Incidente" or "Problema".
    Respond EXCLUSIVELY in JSON with the keys: 
    - "category"
    - "service_type"
    - "support_level"
    - "category_justification"

    Examples:
    Ticket: "oi esqueci minha senha do passaporte e precso confirmar matricula hj me ajuda pfvr!!"
    {"category": "Requisição", "service_type": "Acesso", "support_level": 1, "category_justification": "Pedido de recuperacao de credencial. Procedimento padrao de acesso."}

    Ticket: "O projetor da sala 104 do Pantanal nao liga e os alunos ja estao aqui. Ajuda urgente!"
    {"category": "Incidente", "service_type": "Hardware", "support_level": 2, "category_justification": "Falha em equipamento que estava em funcionamento, interrompendo a atividade."}

    Ticket: "Problemas graves na rede UFMS-ADM no Campus de Tres Lagoas. Varios docentes relatando queda de conexao."
    {"category": "Problema", "service_type": "Redes", "support_level": 3, "category_justification": "Instabilidade afetando multiplos usuarios, exigindo analise de causa raiz."}

    Ticket: "Solicito a formatacao e instalacao de softwares basicos nos 15 computadores do laboratorio 3"
    {"category": "Requisição", "service_type": "Infraestrutura", "support_level": 2, "category_justification": "Pedido planejado para preparacao de ambiente, nao e uma falha inesperada."}
    """
    
    # Aqui o código pega o texto do chamado do usuário
    ticket_text = state.get("ticket", {}).get("free_text", "")
    
    # Aqui nós disparamos as instruções (com os exemplos) + o chamado do usuário para a IA
    response_data = call_llm(system_prompt, f"Ticket: {ticket_text}")
    
    # Retornamos a resposta formatada para o LangGraph
    partial = dict(state.get("response", {}))
    partial["category"] = response_data.get("category", "Indefinida")
    partial["service_type"] = response_data.get("service_type", "Geral")
    partial["support_level"] = response_data.get("support_level", 1)
    partial["category_justification"] = response_data.get("category_justification", "Sem justificativa")
    
    return {"response": partial}
    