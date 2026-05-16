from core.state.state import State
from utilities.ingest_incident_ticket import IncidentTicket
from pydantic import ValidationError

import uuid

def ingest_incident(state: State) -> dict:

    incident = state.get("incident")
    incident["id"] = str(uuid.uuid4())

    try:
        # Validando e processando os dados
        validated_incident = IncidentTicket.model_validate(incident)
    
        # Atualiza os campos com os dados validados
        normalized_incident = validated_incident.model_dump(mode='json')

    # Caso aconteça algum erro de validação
    except ValidationError as error:
        incident["alert_draft"] = error.json()

    return {
        "incident": normalized_incident
    }
