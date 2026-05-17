import json
import random

from config import DATA_REQUEST_PATH, DATA_INCIDENT_PATH, SHUFFLED_DATA_PATH

# 1. Carrega o primeiro arquivo JSON
with open(DATA_REQUEST_PATH, "r", encoding="utf-8") as f:
    request_data = json.load(f)

# 2. Carrega o segundo arquivo JSON
with open(DATA_INCIDENT_PATH, "r", encoding="utf-8") as f:
    incident_data = json.load(f)

# 3. Junta as duas listas de objetos
shuffled_data = request_data + incident_data

# 4. EMBARALHA os registros de forma totalmente aleatória
# Nota: Esta função modifica a própria lista 'shuffled_data'
random.shuffle(shuffled_data)

# 5. Salva a nova base de dados unificada e aleatória
with open(SHUFFLED_DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(shuffled_data, f, indent=4, ensure_ascii=False)

print(f"Sucesso! {len(shuffled_data)} registros unidos e distribuídos aleatoriamente.")