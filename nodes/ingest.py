from state import State
from utilities.ingest_ticket import IngestTicket
from pydantic import ValidationError

def ingest(state: State) -> dict:
    """
    Valida o JSON de entrada e normaliza o texto.
    """
    # Resgata a entrada do JSON
    raw_ticket = state.get("ticket")

    try:
        # Validando e processando os dados
        validated_ticket = IngestTicket.model_validate(raw_ticket)
    
        # Atualiza os campos com os dados validados
        normalized_ticket = validated_ticket.model_dump(mode='json')

    # Caso aconteça algum erro de validação
    except ValidationError as error:
        partial = dict(state.get("response", {}))
        partial["response_draft"] = error.json()
        partial["validation_status"] = False

        return {"ticket": normalized_ticket, "response": partial}

    return {"ticket": normalized_ticket}
