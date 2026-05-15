# Hackathon

## Membros do Time 1
- Davi Gaborim 
- Murilo Bassan
- Paola Campos
- Wellington Cintra

## Processo escolhido
3.1. AGETIC - Triagem Inteligente de Chamados de Suporte de TIC.

## Responsabilidades de cada integrante
Estão dispostas no Issues do repositório.

## Tipos de commit

| Tipo       | Descrição                                                                 |
|------------|---------------------------------------------------------------------------|
| `feat`     | Adição de nova funcionalidade                                             |
| `fix`      | Correção de bug                                                           |
| `docs`     | Mudanças apenas na documentação                                           |
| `style`    | Alterações de formatação, como identação, sem alterar lógica              |
| `refactor` | Refatorações (alteração de código que não corrige nem adiciona funcionalidade) |
| `test`     | Adição ou alteração de testes                                             |
| `chore`    | Tarefas de manutenção (ex: build, configs, atualização de dependências)   |
| `add`      | Adição de novos arquivos, recursos (assets) ou textos estáticos           |

---

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/murilo-bassan/hackathon-mda.git
cd hackathon-mda
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

Edite o `.env`:

```env
OPENROUTER_API_KEY=sk-or-...   # Sua chave da OpenRouter
MODEL_NAME=google/gemma-3-27b-it  # Modelo a usar (padrão)
```

> **Dica:** Qualquer modelo disponível na [OpenRouter](https://openrouter.ai/models) pode ser usado. O padrão é `google/gemma-3-27b-it`.

---

## Como Rodar

### Interface Web (Streamlit) — recomendado para demos

```bash
streamlit run app.py
```

Acesse em: `http://localhost:8501`

---

### Modo Batch (CLI)

```bash
python main.py
```

O modo batch processa tickets do dataset em faixa configurável. Edite `main.py` para definir o intervalo:

```python
START_INDEX = 0   # índice de início (inclusive, 0-based)
END_INDEX   = 10  # índice de fim (exclusive)
```

Ao finalizar, executa automaticamente `run_accuracy()` para calcular as métricas.

## Testes

O projeto conta com suíte de testes automatizados em `tests/`:

```bash
# Rodar todos os testes
pytest tests/

# Com verbose
pytest tests/ -v

# Apenas testes de nós
pytest tests/test_nodes.py -v

# Apenas testes de arestas
pytest tests/test_edges.py -v

# Execução de todos os testes com cobertura
pytest tests/ -v --cov=nodes --cov=utilities --cov-report=term-missing
```
