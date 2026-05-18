from datetime import datetime, timezone
import json
from process_incident.utilities.config import DATA_PATH, RESPONSES_PATH
from general_process.utilities.normalize_text import normalize_str

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_dataset = json.load(f)

DATASET_INDEX = {
    ticket["id"]: ticket
    for ticket in raw_dataset
}

def run_accuracy() -> list:

    response_files = sorted(RESPONSES_PATH.glob("*.json"))

    errors = []

    responses: list[dict] = []
    for file_path in response_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            responses.append(data)

    category_hits            = 0
    critical_hits            = 0
    scope_hits               = 0
    responsible_person_hits  = 0
    processed_total          = 0

    for response in responses:

        ticket_id = response.get("id")

        # Ignora respostas sem correspondência no dataset
        if ticket_id not in DATASET_INDEX:
            print(f"[AVISO] ticket_id '{ticket_id}' não encontrado no dataset — ignorado.")
            continue

        expected_ticket = expected_ticket(ticket_id)
        processed_total += 1

        # CATEGORY
        predicted_category = normalize_str(response.get("category") or "")
        expected_category  = normalize_str(expected_ticket.get("category") or "")

        if predicted_category == expected_category:
            category_hits += 1
        else:
            errors.append({"ticket_id": ticket_id, "field": "category",
                           "expected": expected_category, "predicted": predicted_category})

        # CRITICAL
        predicted_critical = response.get("critical")
        expected_critical  = expected_ticket.get("critical")

        if predicted_critical == expected_critical:
            critical_hits += 1
        else:
            errors.append({"ticket_id": ticket_id, "field": "critical",
                           "expected": expected_critical, "predicted": predicted_critical})

        # SCOPE
        predicted_scope = normalize_str(response.get("scope") or "")
        expected_scope  = normalize_str(expected_ticket.get("scope") or "")

        if predicted_scope == expected_scope:
            scope_hits += 1
        else:
            errors.append({"ticket_id": ticket_id, "field": "scope",
                           "expected": expected_scope, "predicted": predicted_scope})

        # RESPONSIBLE PERSON
        predicted_responsible = normalize_str(response.get("responsible_person") or "")
        expected_responsible  = normalize_str(expected_ticket.get("responsible_person") or "")

        if predicted_responsible == expected_responsible:
            responsible_person_hits += 1
        else:
            errors.append({"ticket_id": ticket_id, "field": "responsible_person",
                           "expected": expected_responsible, "predicted": predicted_responsible})


    if processed_total == 0:
        print("Nenhum ticket processado. Verifique se a pasta de respostas está correta.")
        raise SystemExit(1)

    category_accuracy           = (category_hits           / processed_total) * 100
    critical_accuracy           = (critical_hits           / processed_total) * 100
    scope_accuracy              = (scope_hits              / processed_total) * 100
    responsible_person_accuracy = (responsible_person_hits / processed_total) * 100

    # ==========================================
    # PRINT FINAL
    # ==========================================

    print("\n" + "=" * 60)
    print("MÉTRICAS DO SISTEMA")
    print("=" * 60)

    print(f"Total de tickets avaliados: {processed_total}")
    print(f"Pedidos de mais informação: {needs_more_info_total}")

    print("\nQUALIDADE DO MODELO")
    print(f"Accuracy Categoria:            {category_accuracy:.2f}%")
    print(f"Accuracy Criticidade:          {critical_accuracy:.2f}%")
    print(f"Accuracy Escopo:               {scope_accuracy:.2f}%")
    print(f"Accuracy Responsável:          {responsible_person_accuracy:.2f}%")

    print("\n" + "=" * 60)

    return errors


def expected_ticket(id: str) -> dict:

    ticket = DATASET_INDEX[id]

    return {
        "category":           ticket["category"],
        "critical":           ticket["critical"],
        "scope":              ticket["scope"],
        "responsible_person": ticket["responsible_person"],
        "needs_more_info":    ticket["needs_more_info"]
    }