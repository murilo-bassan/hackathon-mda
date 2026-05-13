from datetime import datetime, timezone
import json

from graph_builder import graph
from utilities.decide_response import decide_response
import random

# ==========================================
# CARREGA DATASET
# ==========================================
TEST_SIZE = 10

with open("data/data.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

random.seed(42)
dataset = random.sample(dataset, TEST_SIZE)
# ==========================================
# MÉTRICAS
# ==========================================

category_hits = 0
priority_hits = 0
department_hits = 0

resolved_by_llm = 0
routed_to_human = 0

validation_success = 0

total = len(dataset)

# ==========================================
# LOOP
# ==========================================
total_resolution_time = 0.0
closed_same_day = 0

for ticket in dataset:

    state = {
        "ticket": {
            "id":                ticket["id"],
            "timestamp":         ticket["timestamp"],
            "channel":           ticket["channel"],
            "requester_profile": ticket["requester_profile"],
            "free_text":         ticket["free_text"]
        },
        "response": {}
    }

    start_time = datetime.now(timezone.utc)
    final_state = graph.invoke(state)
    end_time = datetime.now(timezone.utc)

    elapsed_seconds = (end_time - start_time).total_seconds()
    total_resolution_time += elapsed_seconds

    response = final_state["response"]

    # ======================================
    # AUTOMAÇÃO
    # ======================================

    next_route = decide_response(final_state)

    if next_route == "draft_response":
        resolved_by_llm += 1
    else:
        routed_to_human += 1

    # ======================================
    # ENCERRADOS NO DIA
    # ======================================

    ticket_date = datetime.fromisoformat(
        ticket["timestamp"].replace("Z", "+00:00")
    ).date()

    resolved_today = (
        next_route == "draft_response" and
        ticket_date == datetime.now(timezone.utc).date()
    )

    if resolved_today:
        closed_same_day += 1


    # ======================================
    # CATEGORY ACCURACY
    # ======================================

    predicted_category = (
        response["category"]
        .strip()
        .lower()
    )

    expected_category = (
        ticket["category"]
        .strip()
        .lower()
    )

    if predicted_category == expected_category:
        category_hits += 1

    # ======================================
    # PRIORITY ACCURACY
    # ======================================

    predicted_priority = (
        str(response["resulting_priority"])
        .strip()
        .lower()
    )

    expected_priority = (
        ticket["priority"]
        .strip()
        .lower()
    )

    
    priority_map = {
        "baixa":   "1",
        "média":   "2",
        "media":   "2",
        "alta":    "3",
        "crítica": "4",
        "critica": "4",
    }

    expected_priority = priority_map.get(
        expected_priority,
        expected_priority
    )

    if predicted_priority == expected_priority:
        priority_hits += 1

    # ======================================
    # DEPARTMENT ACCURACY
    # ======================================

    predicted_department = (
        response["department"]
        .strip()
        .lower()
    )

    expected_department = (
        ticket["suggested_sector"]
        .strip()
        .lower()
    )

    if expected_department in predicted_department:
        department_hits += 1

    # ======================================
    # VALIDAÇÃO
    # ======================================

    if response.get("validation_status") is True:
        validation_success += 1

    # ======================================
    # AUTOMAÇÃO
    # ======================================

    next_route = decide_response(final_state)

    if next_route == "draft_response":
        resolved_by_llm += 1
    else:
        routed_to_human += 1

# ==========================================
# RESULTADOS
# ==========================================

avg_resolution_time = total_resolution_time / total
print(f"Tempo médio de resolução: {avg_resolution_time:.2f}s")

same_day_rate = (closed_same_day / total) * 100
print(f"Encerrados no dia: {closed_same_day}")
print(f"Taxa de encerramento no dia: {same_day_rate:.2f}%")

category_accuracy = (
    category_hits / total
) * 100

priority_accuracy = (
    priority_hits / total
) * 100

department_accuracy = (
    department_hits / total
) * 100

automation_rate = (
    resolved_by_llm / total
) * 100

validation_rate = (
    validation_success / total
) * 100

# ==========================================
# PRINT FINAL
# ==========================================

print("\n" + "=" * 60)
print("MÉTRICAS DO SISTEMA")
print("=" * 60)

print(f"Total de tickets: {total}")

print("\nQUALIDADE DO MODELO")
print(f"Accuracy Categoria:    {category_accuracy:.2f}%")
print(f"Accuracy Prioridade:   {priority_accuracy:.2f}%")
print(f"Accuracy Departamento: {department_accuracy:.2f}%")

print("\nINDICADORES DE SERVIÇO")
print(f"Tempo médio de resolução: {avg_resolution_time:.2f}s")
print(f"Encerrados no dia:        {closed_same_day}/{total}")
print(f"Taxa de encerramento:     {same_day_rate:.2f}%")

print("\nAUTOMAÇÃO")
print(f"Resolvidos pela LLM:    {resolved_by_llm}")
print(f"Encaminhados p/ humano: {routed_to_human}")
print(f"Taxa de automação:      {automation_rate:.2f}%")

print("\nVALIDAÇÃO")
print(f"Taxa de validação: {validation_rate:.2f}%")

print("\n" + "=" * 60)