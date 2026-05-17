from process_incident.core.state.incident_state import State
from process_incident.utilities.ingest_incident_ticket import IncidentTicket
from pydantic import ValidationError

import uuid

def ingest_incident(state: State) -> dict:

    incident = dict(state.get("incident") or {})

    try:
        if (not incident.get("id")):
            incident["id"] = str(uuid.uuid4())
        
        # Validando e processando os dados
        validated_incident = IncidentTicket.model_validate(incident)
    
        # Atualiza os campos com os dados validados
        normalized_incident = validated_incident.model_dump(mode='json')

        normalized_incident["validation_status"] = True

    # Caso aconteça algum erro de validação
    except ValidationError as error:
        incident["alert_draft"] = error.json()
        incident["validation_status"] = False

        return {
            "incident": incident
        }

    return {
        "incident": normalized_incident
    }
