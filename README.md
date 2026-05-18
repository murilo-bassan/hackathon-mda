# Hackathon Meta 3 — UFMS Apoia MDA
## Automação de Processos com LangGraph

> Agentes inteligentes para triagem automática de chamados de TIC (Processo 3.1) e incidentes de segurança da informação (Processo 3.5) da AGETIC/UFMS.

### Membros do Time 1
- Davi Gaborim 
- Murilo Bassan
- Paola Campos
- Wellington Cintra

### Responsabilidades de cada integrante
Estão dispostas no Issues do repositório.

## Processos escolhidos
**3.1. AGETIC -** Triagem Inteligente de Chamados de Suporte de TIC

**3.5. AGETIC -** Triagem de Incidentes de Segurança da Informação

### Documentação
Está localizada na pasta `docs` no arquivo `documentation.md` no repositório.

### Vídeo do demoday
Os slides usados na apresentação estão na pasta `docs` no arquivo `hackathon.pdf` no repositório.

Link do Youtube: [https://www.youtube.com/watch?v=MUWsZPIKGfQ](https://www.youtube.com/watch?v=MUWsZPIKGfQ)

---

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

## 📖 Visão Geral

### O Problema

A AGETIC (Agência de Tecnologia da Informação e Comunicação da UFMS) opera dois fluxos críticos de atendimento que dependem intensamente de leitura e interpretação de texto livre:

**Processo 3.1 — Triagem Inteligente de Chamados de Suporte de TIC**

A Central de Serviços da AGETIC recebe centenas de chamados por semana via quatro canais (sistema OTRS, telefone, balcão e e-mail). No início de cada turno, o analista de primeiro nível executa manualmente as seguintes etapas para cada chamado: leitura do texto livre, avaliação de suficiência de informação, categorização (Requisição / Incidente / Problema), identificação do tipo de serviço no Catálogo de TIC, cálculo de urgência e impacto, derivação da prioridade, definição do setor responsável (N1/N2/N3) e rascunho da resposta ao usuário. Esse trabalho é altamente repetitivo e sujeito a inconsistências humanas sob volume elevado. Os indicadores oficiais da AGETIC — "Chamados Diários Encerrados" e "Tempo de Atendimento Médio" — medem exatamente o tipo de ganho que a automação parcial pode produzir.

**Processo 3.5 — Triagem de Incidentes de Segurança da Informação**

A ETIR (Equipe de Tratamento e Resposta a Incidentes Cibernéticos) recebe relatos de incidentes de segurança por múltiplos canais. Para cada incidente, a equipe precisa: classificar a criticidade (Crítico / Não-crítico), identificar categoria (phishing, ransomware, acesso não autorizado, etc.), mapear sistemas afetados, localizar o responsável técnico cruzando o relato com o inventário de ativos, recomendar passos de contenção do playbook, redigir o e-mail de alerta com tom proporcional à criticidade e gerar o template de Relatório Parcial. Trata-se de um processo com janela de tempo curta e alto risco de erro humano sob pressão — exatamente onde a consistência de um agente é mais valiosa.

### Benefícios Esperados da Automação

| Benefício | Processo 3.1 | Processo 3.5 |
|---|---|---|
| Redução do tempo de triagem | ✅ Priorização imediata sem espera de turno | ✅ Acionamento do responsável em segundos |
| Consistência de decisões | ✅ Categorização uniforme baseada no Catálogo de TIC | ✅ Classificação de criticidade padronizada |
| Auditabilidade | ✅ Justificativa textual em todos os campos | ✅ Log estruturado por incidente |
| Escalada segura | ✅ Chamados complexos vão para fila humana | ✅ Fail-safe encaminha para ETIR se LLM falhar |
| Geração de documentos | ✅ Rascunho de resposta ao usuário | ✅ E-mail de alerta + template de relatório |

---

## ⚙️ Pré-requisitos e Configuração Completa

### Versão do Python

**Python 3.11 ou superior** é obrigatório. O projeto usa f-strings com aspas aninhadas (sintaxe válida a partir do Python 3.12 em alguns casos), `TypedDict` e `match` patterns. Recomenda-se Python 3.12.

Verifique com:
```bash
python --version
```

### Passo a Passo de Instalação

**1. Clone o repositório e entre na pasta:**
```bash
git clone https://github.com/murilo-bassan/hackathon-mda.git
cd hackathon-mda-main
```

**2. Crie e ative um ambiente virtual:**
```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
```

**3. Instale as dependências:**
```bash
pip install -r requirements.txt
```

O arquivo `requirements.txt` contém:
```
langgraph
langgraph-prebuilt
langgraph-sdk
langsmith>=0.7.31
langchain
langchain-community
langchain-core>=1.2.28
langchain-openai>=1.1.14
langchain-text-splitters>=1.1.2
python-dotenv
requests
pandas
pydantic
pytest
pytest-cov
streamlit
aiohttp>=3.13.4
Pygments>=2.20.0
cryptography>=46.0.7
```

**4. Configure as variáveis de ambiente:**
```bash
cp .env.example .env
```
Edite o arquivo `.env` com os seus valores reais.

### Tabela de Variáveis de Ambiente

| Variável | Obrigatória | Descrição | Como Obter |
|---|---|---|---|
| `OPENROUTER_API_KEY` | ✅ **Sim** | Chave de API do OpenRouter, gateway unificado de acesso a modelos LLM (open-source e proprietários). Todas as chamadas ao LLM passam por aqui via endpoint `/api/v1/chat/completions`. | Acesse [openrouter.ai](https://openrouter.ai), crie uma conta e gere uma chave em **Settings → API Keys**. No hackathon, a coordenação fornece a chave com cota controlada. |
| `MODEL_NAME` | ❌ Opcional | Identificador do modelo LLM a usar nas chamadas. **Default:** `google/gemma-3-27b-it`. Deve ser um modelo disponível no OpenRouter. Recomenda-se modelos de até 30B parâmetros para uso em produção local. | Consulte o catálogo em [openrouter.ai/models](https://openrouter.ai/models). Exemplos válidos: `google/gemma-3-27b-it`, `mistralai/mistral-7b-instruct`, `meta-llama/llama-3-8b-instruct`. |
| `LANGSMITH_API_KEY` | ❌ Opcional | Chave para observabilidade e rastreamento de execuções via LangSmith. Quando configurada, todas as chamadas ao LangGraph são registradas com trace completo no painel do LangSmith. | Acesse [smith.langchain.com](https://smith.langchain.com), crie uma conta e gere uma chave em **Settings → API Keys**. |
| `LANGCHAIN_TRACING_V2` | ❌ Opcional | Ativa o tracing automático via LangSmith. Defina como `true` para habilitar. | Basta adicionar `LANGCHAIN_TRACING_V2=true` ao `.env` junto com a `LANGSMITH_API_KEY`. |
| `LANGCHAIN_PROJECT` | ❌ Opcional | Nome do projeto no LangSmith onde as execuções serão agrupadas. | Defina qualquer string descritiva, ex: `hackathon-meta3`. |

**Exemplo de `.env` completo:**
```dotenv
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
MODEL_NAME=google/gemma-3-27b-it
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxx
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=hackathon-meta3
```

---

## 🚀 Como Executar

### Modo 1: Grafo Geral (processa ambos os processos com dataset misto)

O arquivo `general_process/data/shuffled_data.json` contém chamados e incidentes misturados. O grafo pai classifica automaticamente cada entrada e encaminha ao subgrafo correto.

```bash
python main.py
```

O script processa os primeiros `END_INDEX` (padrão: 10) registros do dataset misto, imprime os erros de acurácia ao final e salva os artefatos em `general_process/artifacts/`.

### Modo 2: Apenas Processo 3.1 (Triagem de Chamados)

Processa exclusivamente o dataset `process_request/data/data.json`. Exibe análise do dataset antes de executar e calcula a acurácia ao final.

```bash
python main_request.py
```

### Modo 3: Apenas Processo 3.5 (Triagem de Incidentes)

Processa exclusivamente o dataset `process_incident/data/incidents.json`.

```bash
python main_incident.py
```

### Modo 4: Interface Web (Streamlit)

O projeto inclui uma interface visual com três páginas.

```bash
streamlit run app.py
```

As páginas disponíveis (em `pages/`) são:
- `app_general.py` — executa o grafo geral com input via formulário
- `app_requests.py` — executa o processo 3.1
- `app_incidents.py` — executa o processo 3.5

### Modo 5: Testes Unitários

```bash
# Todos os testes
pytest

# Com relatório de cobertura
pytest --cov=process_request --cov=process_incident --cov-report=term-missing

# Apenas processo 3.1
pytest process_request/tests/

# Apenas processo 3.5
pytest process_incident/tests/
```

### Artefatos Gerados

Após a execução, os seguintes arquivos são gerados automaticamente:

| Artefato | Caminho | Descrição |
|---|---|---|
| JSON individual por chamado | `process_request/artifacts/responses_json/ticket_<id>.json` | Resultado completo da triagem de cada chamado |
| CSV consolidado (3.1) | `process_request/artifacts/report.csv` | Todos os chamados processados em uma linha por registro |
| JSON individual por incidente | `process_incident/artifacts/responses_json/incident_<id>.json` | Resultado completo da triagem de cada incidente |
| CSV consolidado (3.5) | `process_incident/artifacts/report.csv` | Todos os incidentes processados |
| Fila humana | `process_request/data/human_queue.json` | Chamados de alta prioridade ou categoria complexa enfileirados para analista humano |
| Log estruturado | `general_process/artifacts/logs/execucao.log` | Log JSON de todas as execuções com tokens consumidos |
| Grafo PNG | `docs/graph.png` | Visualização do grafo compilado |

---

## 📥 Exemplos de Entrada e Saída

### Processo 3.1 — Exemplo de Chamado de Suporte

**Payload de entrada (JSON):**
```json
{
  "id": "TKT-2026-0001",
  "timestamp": "2026-02-15T08:14:00Z",
  "channel": "Sistema de Chamados",
  "requester_profile": "Estudante",
  "free_text": "Oiii, esqueci minha senha do passaporte ufms e n consigo acessar o sigaa pra ver minhas aulas 😭😭 ajuda plsss!!!!"
}
```

**Saída esperada (JSON):**
```json
{
  "ticket_id": "TKT-2026-0001",
  "category": "Requisição",
  "category_justification": "Solicitação de recuperação de credencial do Passaporte UFMS.",
  "urgency": 2,
  "impact": 1,
  "resulting_priority": 2,
  "priority_justification": "A prioridade é baixa pois trata-se de um problema de acesso individual (Baixo Impacto) e o usuário pode seguir o fluxo padrão de recuperação (Baixa Urgência).",
  "service_type": "Passaporte UFMS",
  "support_level": 1,
  "department": "N1 - Atendimento Direto",
  "response_draft": "Olá! Para recuperar sua senha do Passaporte UFMS, por favor acesse passaporte.ufms.br e clique em 'Recuperar Senha'. Siga as instruções enviadas para o seu e-mail alternativo cadastrado. ANS: 12 horas.",
  "closing_message": "Seu chamado foi encerrado pela equipe da AGETIC/UFMS. Caso o problema persista, reabra o chamado ou entre em contato: suporte.agetic@ufms.br | (67) 3345-7292.",
  "needs_more_info": false,
  "info_justification": "",
  "validation_status": true
}
```

**Payload de entrada para chamado de alta prioridade (vai para fila humana):**
```json
{
  "id": "TKT-2026-0099",
  "timestamp": "2026-03-01T14:00:00Z",
  "channel": "Balcão",
  "requester_profile": "Técnico-Administrativo",
  "free_text": "O SIGAA está completamente fora do ar em todo o campus. Não consigo acessar pelo sistema nem pelo celular. Outros servidores também relatam o mesmo problema."
}
```

**Saída esperada (chamado escalado para fila humana):**
```json
{
  "ticket_id": "TKT-2026-0099",
  "category": "Problema",
  "urgency": 4,
  "impact": 4,
  "resulting_priority": 4,
  "service_type": "Sistema Acadêmico",
  "department": "N2 - Sistemas Administrativos",
  "response_draft": "[FILA HUMANA] Encaminhado ao analista responsável.",
  "validation_status": true
}
```
> Nota: chamados do tipo "Problema" **sempre** são escalados para a fila humana, independentemente da prioridade — conforme a regra `decide_response()`.

---

### Processo 3.5 — Exemplo de Incidente de Segurança

**Payload de entrada (JSON):**
```json
{
  "id": "INC-2026-0001",
  "timestamp": "2026-03-10T07:42:00Z",
  "free_text": "Recebi um e-mail suspeito pedindo para confirmar meus dados do Passaporte UFMS em um link externo. O link parece falso. Não cliquei, mas vários colegas do meu laboratório receberam a mesma mensagem."
}
```

**Saída esperada (JSON):**
```json
{
  "id": "INC-2026-0001",
  "category": "phishing",
  "category_justification": "Campanha de e-mails fraudulentos visando credenciais do Passaporte UFMS.",
  "critical": true,
  "critical_justification": "Afeta múltiplos usuários do laboratório e visa comprometimento de credenciais institucionais.",
  "scope": "multiplos_usuarios",
  "affected_systems": "E-mail Institucional, Passaporte UFMS",
  "responsible_person": "Ana Paula Ramos",
  "contact_info": "ana.ramos@agetic.ufms.br | (67) 3345-7225",
  "containment_steps": [
    "Bloquear o link malicioso no firewall (Fortigate)",
    "Emitir alerta para todos os usuários não clicarem no link",
    "Verificar logs do SIEM/Wazuh para identificar usuários que clicaram",
    "Forçar reset de senha dos usuários potencialmente comprometidos",
    "Registrar o domínio malicioso na blacklist do antispam"
  ],
  "containment_justification": "Priorizadas ações de bloqueio e rastreamento para campanha de phishing com múltiplos alvos.",
  "alert_draft": "Assunto: [CRÍTICO] Incidente de Phishing Detectado — Ação Imediata Necessária\n\nCaro(a) Ana Paula Ramos,\n\nA ETIR detectou uma campanha de phishing ativa visando credenciais do Passaporte UFMS...",
  "report_template": "RELATÓRIO PARCIAL DE INCIDENTE DE SEGURANÇA\n==================================================\n1. IDENTIFICAÇÃO DO INCIDENTE\nID: INC-2026-0001\nData/Hora: 2026-03-10T07:42:00Z\n..."
}
```

---

## 📁 Estrutura de Diretórios

```
hackathon-mda-main/
├── .env.example                    # Template de variáveis de ambiente
├── .gitignore
├── requirements.txt                # Dependências Python
├── main.py                         # Entry point — grafo geral (ambos os processos)
├── main_request.py                 # Entry point — apenas processo 3.1
├── main_incident.py                # Entry point — apenas processo 3.5
├── app.py                          # Entry point — interface Streamlit
│
├── docs/
│   ├── graph.png                   # Visualização do grafo (gerada automaticamente)
│   ├── documentation.md            # Documentação original da equipe
│   └── hackathon.pdf               # Slides da apresentação da equipe
│
├── general_process/                # Grafo pai — orquestrador central
│   ├── core/
│   │   ├── graph_builder.py        # Constrói o StateGraph principal
│   │   ├── nodes/
│   │   │   ├── normalize_input.py  # Nó: normaliza texto de entrada
│   │   │   ├── classify_input.py   # Nó: classifica como request ou incident
│   │   │   ├── request_workflow.py # Nó: wrapper do subgrafo 3.1
│   │   │   └── incident_workflow.py# Nó: wrapper do subgrafo 3.5
│   │   └── state/
│   │       └── state.py            # Estado do grafo pai (State TypedDict)
│   ├── data/
│   │   └── shuffled_data.json      # Dataset misto (chamados + incidentes)
│   ├── prompts/
│   │   └── classify_input_prompt.md# Prompt de classificação request vs incident
│   └── utilities/
│       ├── config.py               # Caminhos de ficheiros (pathlib)
│       ├── decide_input.py         # Função de roteamento condicional
│       ├── utils.py                # call_llm() — wrapper HTTP para OpenRouter
│       ├── prompt_loader.py        # Carrega prompts de ficheiros .md
│       ├── normalize_text.py       # Normalização de texto (minúsculas, acentos)
│       ├── clean_text.py           # Limpeza de texto
│       ├── load_input.py           # Carrega datasets JSON
│       ├── logger_config.py        # Configuração do logger estruturado
│       ├── process_ticket.py       # Orquestra o processamento de cada ticket
│       └── save_graph_visualization.py # Salva PNG do grafo
│
├── process_request/                # Processo 3.1 — Triagem de Chamados TIC
│   ├── core/
│   │   ├── subgraph_request_builder.py  # Constrói o subgrafo 3.1
│   │   ├── nodes/
│   │   │   ├── ingest.py           # Nó: valida e normaliza com Pydantic
│   │   │   ├── validate_input.py   # Nó: LLM verifica suficiência de info
│   │   │   ├── classify_type.py    # Nó: LLM categoriza e mapeia ao catálogo
│   │   │   ├── score_priority.py   # Nó: LLM (paralelo) + cálculo determinístico
│   │   │   ├── draft_response.py   # Nó: LLM rascunha resposta com few-shot
│   │   │   ├── draft_request.py    # Nó: LLM pede info faltante ao usuário
│   │   │   ├── queue_only.py       # Nó: serializa para fila humana
│   │   │   └── emit.py             # Nó: serializa saída final (JSON + CSV)
│   │   └── state/
│   │       ├── request_state.py    # State TypedDict (ticket + response)
│   │       ├── ticket.py           # TypedDict do ticket de entrada
│   │       └── response.py         # TypedDict da resposta processada
│   ├── data/
│   │   ├── data.json               # Dataset de chamados sintéticos (ground truth)
│   │   └── human_queue.json        # Fila de chamados para analistas humanos
│   ├── prompts/                    # Prompts versionados em Markdown
│   │   ├── classify_type_prompt.md
│   │   ├── validate_input_prompt.md
│   │   ├── score_urgency_prompt.md
│   │   ├── score_impact_prompt.md
│   │   ├── justify_priority_prompt.md
│   │   ├── draft_response_prompt.md
│   │   └── draft_request_prompt.md
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_nodes.py
│   │   └── test_edges.py
│   └── utilities/
│       ├── config.py               # Caminhos de ficheiros
│       ├── ingest_ticket.py        # Modelo Pydantic IngestTicket
│       ├── decide_content.py       # Roteamento: needs_more_info?
│       ├── decide_response.py      # Roteamento: draft_response vs queue_only
│       ├── validation_response.py  # Roteamento: falha Pydantic → emit
│       ├── build_few_shot.py       # Constrói exemplos few-shot por departamento
│       ├── normalize.py            # normalize_str() para comparação de strings
│       ├── accuracy.py             # Cálculo de acurácia vs ground truth
│       └── dataset_analyzer.py     # Análise estatística do dataset
│
├── process_incident/               # Processo 3.5 — Triagem de Incidentes SI
│   ├── core/
│   │   ├── subgraph_incident_builder.py # Constrói o subgrafo 3.5
│   │   ├── nodes/
│   │   │   ├── ingest_incident.py  # Nó: valida com Pydantic
│   │   │   ├── classify_criticality.py  # Nó: LLM classifica criticidade
│   │   │   ├── lookup_owner.py     # Nó: busca determinística no inventário
│   │   │   ├── recommend_containment.py # Nó: LLM sugere contenção do playbook
│   │   │   ├── draft_alert.py      # Nó: LLM rascunha e-mail de alerta
│   │   │   ├── request_report.py   # Nó: LLM gera template de relatório
│   │   │   └── emit_incident.py    # Nó: serializa saída final (JSON + CSV)
│   │   └── state/
│   │       ├── incident_state.py   # State TypedDict (incident)
│   │       └── incident.py         # TypedDict do incidente
│   ├── data/
│   │   ├── incidents.json          # Dataset de incidentes sintéticos (ground truth)
│   │   ├── inventory.json          # Inventário mock de sistemas e responsáveis
│   │   └── playbook.md             # Playbook de contenção por categoria
│   ├── prompts/
│   │   ├── classify_criticality_prompt.md
│   │   ├── recommend_containment_prompt.md
│   │   ├── draft_alert_prompt.md
│   │   └── request_report_prompt.md
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_nodes.py
│   │   └── test_edges.py
│   └── utilities/
│       ├── config.py
│       ├── ingest_incident_ticket.py  # Modelo Pydantic IncidentTicket
│       ├── incident_validation.py     # Roteamento: falha Pydantic → emit_incident
│       ├── find_owner.py              # Busca o dono no inventário por sistema afetado
│       ├── match_term.py              # Regex de palavra completa (sem substring falso-positivo)
│       ├── load_inventory.py          # Carrega inventory.json
│       ├── accuracy.py                # Cálculo de acurácia
│       └── dataset_analyzer.py        # Análise estatística do dataset
│
└── pages/                          # Páginas da interface Streamlit
    ├── app_general.py
    ├── app_incidents.py
    └── app_requests.py
```
