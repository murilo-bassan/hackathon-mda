import json

from nodes.ingest import ingest
from nodes.classify_type import classify_type
from nodes.score_priority import score_priority
from utilities.decide_response import decide_response
import random

# ==========================================
# CARREGA DATASET
# ==========================================
TEST_SIZE = 5

with open("data/data.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

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

    # ======================================
    # CLASSIFICAÇÃO
    # ======================================
    ingest_result = ingest(state)
    state["ticket"]   = ingest_result.get("ticket",   state["ticket"])
    state["response"] = ingest_result.get("response", state["response"])   
    result = classify_type(state)

    state["response"] = result["response"]

    # ======================================
    # PRIORIDADE
    # ======================================

    result = score_priority(state)

    state["response"] = result["response"]

    response = state["response"]

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
        "média":   "3",
        "media":   "3",
        "alta":    "4",
        "crítica": "5",
        "critica": "5",
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

    next_route = decide_response(state)

    if next_route == "draft_response":
        resolved_by_llm += 1
    else:
        routed_to_human += 1

# ==========================================
# RESULTADOS
# ==========================================

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

print("\nCLASSIFICAÇÃO")
print(f"Accuracy Categoria: {category_accuracy:.2f}%")
print(f"Accuracy Prioridade: {priority_accuracy:.2f}%")
print(f"Accuracy Departamento: {department_accuracy:.2f}%")

print("\nAUTOMAÇÃO")
print(f"Resolvidos pela LLM: {resolved_by_llm}")
print(f"Encaminhados para humano: {routed_to_human}")
print(f"Taxa de automação: {automation_rate:.2f}%")

print("\nVALIDAÇÃO")
print(f"Taxa de validação: {validation_rate:.2f}%")

print("\n" + "=" * 60)