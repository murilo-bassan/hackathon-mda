from datetime import datetime, timezone
import json
from process_request.utilities.config import DATA_PATH, RESPONSES_PATH
from process_request.utilities.normalize import normalize_str
from process_request.utilities.decide_response import decide_response

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_dataset = json.load(f)

DATASET_INDEX = {
    ticket["id"]: ticket
    for ticket in raw_dataset
}

def run_accuracy() -> list:

    response_files = sorted(RESPONSES_PATH.glob("*.json"))

    responses: list[dict] = []
    for file_path in response_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            responses.append(data)



    category_hits      = 0
    priority_hits      = 0
    department_hits    = 0
    resolved_by_llm    = 0
    routed_to_human    = 0
    closed_same_day    = 0
    processed_total    = 0
    needs_more_info_total = 0
    t_mae_priority = 0
    mae_priority = 0
    errors = 0

    for response in responses:

        ticket_id = response.get("ticket_id")

        # Ignora respostas sem correspondência no dataset
        if ticket_id not in DATASET_INDEX:
            errors+=1
            print(f"[AVISO] ticket_id '{ticket_id}' não encontrado no dataset — ignorado.")
            continue

        if response.get("needs_more_info") is True:
            needs_more_info_total += 1
            continue

        expected_ticket = DATASET_INDEX[ticket_id]
        processed_total += 1


        next_route = decide_response(response.get("resulting_priority"),response.get("category"))

        if next_route == "draft_response":
            resolved_by_llm += 1
        else:
            routed_to_human += 1

        # ======================================
        # ENCERRADOS NO DIA
        # ======================================

        try:
            ticket_date = datetime.fromisoformat(
                expected_ticket["timestamp"].replace("Z", "+00:00")
            ).date()

            if (next_route == "draft_response" and ticket_date == datetime.now(timezone.utc).date()):
                closed_same_day += 1

        except Exception:
            pass

        #category
        predicted_category = normalize_str(response.get("category") or "")
        expected_category  = normalize_str(expected_ticket.get("category") or "")

        if predicted_category == expected_category:
            category_hits += 1

        #priority
        predicted_priority = response.get("resulting_priority", 0)
        expected_priority = expected_ticket.get("resulting_priority",0)

        t_mae_priority+= abs(predicted_priority - expected_priority)

        if predicted_priority == expected_priority:
            priority_hits += 1

        #departament
        predicted_department = normalize_str(response.get("department") or "")
        expected_department  = normalize_str(expected_ticket.get("department") or "")

        # Aceita match parcial (ex: "n2 - suporte de campo" in "n2 - suporte de campo e field")
        if expected_department and expected_department in predicted_department:
            department_hits += 1


    if processed_total == 0:
        print("Nenhum ticket processado. Verifique se a pasta de respostas está correta.")
        raise SystemExit(1)


    category_accuracy   = (category_hits   / processed_total) * 100
    priority_accuracy   = (priority_hits   / processed_total) * 100
    department_accuracy = (department_hits / processed_total) * 100
    automation_rate     = ((resolved_by_llm+needs_more_info_total) / (processed_total+needs_more_info_total)) * 100
    same_day_rate       = (closed_same_day / processed_total) * 100
    mae_priority        = t_mae_priority / processed_total

    # ==========================================
    # PRINT FINAL
    # ==========================================

    print("\n" + "=" * 60)
    print("MÉTRICAS DO SISTEMA")
    print("=" * 60)

    print(f"Total de tickets avaliados: {processed_total}")
    print(f"Pedidos de mais informação: {needs_more_info_total}")

    print("\nQUALIDADE DO MODELO")
    print(f"Accuracy Categoria:    {category_accuracy:.2f}%")
    print(f"Accuracy Prioridade:   {priority_accuracy:.2f}%")
    print(f"MAE Prioridade: {mae_priority:.2f}")
    print(f"Accuracy Departamento: {department_accuracy:.2f}%")

    print("\nINDICADORES DE SERVIÇO")
    print(f"Encerrados no dia:    {closed_same_day}/{processed_total}")
    print(f"Taxa de encerramento: {same_day_rate:.2f}%")

    print("\nAUTOMAÇÃO")
    print(f"Resolvidos pela LLM:    {resolved_by_llm+needs_more_info_total}")
    print(f"Encaminhados p/ humano: {routed_to_human}")
    print(f"Taxa de automação:      {automation_rate:.2f}%")

    print("\n" + "=" * 60)

    return errors

def expected_ticket(id: str) -> dict:

    ticket = DATASET_INDEX[id]

    return {
        "category": ticket["category"],
        "priority": ticket["resulting_priority"],
        "department": ticket["department"],
        "needs_more_info": ticket["needs_more_info"]
    }