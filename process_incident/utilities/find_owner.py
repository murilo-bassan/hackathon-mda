from process_incident.utilities.match_term import match_term

def find_owner(affected_systems: str, inventory: list[dict]) -> dict:
    """
    Função pura: percorre o inventário e retorna o registro cujos aliases
    aparecem como palavras completas no texto de sistemas afetados.
    Retorna o registro "Desconhecido" como fallback.
    """
    text_lower = affected_systems.lower()

    for entry in inventory:
        if entry["system"].lower() == "desconhecido":
            continue
        if match_term(entry["system"], text_lower):
            return entry
        for alias in entry["aliases"]:
            if match_term(alias, text_lower):
                return entry

    return next(
        (e for e in inventory if e["system"].lower() == "desconhecido"),
        {
            "responsible_person": "ETIR", 
            "contact_info": "etir@agetic.ufms.br"
        } # default info
    )