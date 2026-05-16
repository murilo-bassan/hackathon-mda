from general_process.utilities.clean_text import clean_text
from process_request.core.state.request_state import State
from process_request.utilities.ingest_ticket import IngestTicket
from pydantic import ValidationError

import uuid

def ingest(state: State) -> dict:
    """
    Valida o JSON de entrada e normaliza o texto.
    """
    # Resgata a entrada do JSON
    raw_ticket = dict(state.get("ticket") or {})

    partial = dict(state.get("response", {}))

    try:
        if (not raw_ticket.get("id")):
            raw_ticket["id"] = str(uuid.uuid4())
        
        # Validando e processando os dados
        validated_ticket = IngestTicket.model_validate(raw_ticket)
    
        # Atualiza os campos com os dados validados
        normalized_ticket = validated_ticket.model_dump(mode='json')

        partial["validation_status"] = True #default validation_status

    # Caso aconteça algum erro de validação
    except ValidationError as error:
        partial["response_draft"] = error.json()
        partial["validation_status"] = False

        return {
            "response": partial
        }

    return {
        "ticket": normalized_ticket,
        "response": partial
    }
