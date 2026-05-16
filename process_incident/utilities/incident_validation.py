from process_incident.core.state.incident_state import State

def incident_validation(state: State) -> str:
    """
    Se o ingest marcou falha de validação, vai direto para emit; caso contrário segue o fluxo.
    """
    incident = state.get("incident") or {}
    
    if incident.get("validation_status") is False:
        return "emit_incident"
    
    return "classify_criticality"
