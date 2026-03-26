# MiroFish - Documento di Progetto

## Cos'è MiroFish?

MiroFish è un **motore di previsione basato su intelligenza artificiale multi-agente (swarm intelligence)**. Il suo slogan è: *"Motore di intelligenza collettiva semplice e universale, prevedi qualsiasi cosa."*

Il concetto fondamentale: carichi dei "materiali di partenza" (documenti, report, articoli, capitoli di romanzi) e descrivi in linguaggio naturale cosa vuoi prevedere. MiroFish costruisce un mondo digitale abitato da agenti AI che interagiscono tra loro, simulando le dinamiche sociali reali, e produce un report analitico con le previsioni.

---

## Come funziona (Pipeline in 5 fasi)

### Fase 1 - Costruzione del Grafo di Conoscenza
1. L'utente carica documenti (PDF, TXT, Markdown) e descrive il requisito di previsione
2. Il sistema estrae il testo e lo suddivide in chunk
3. Un LLM genera un'ontologia personalizzata (10 tipi di entità + 6-10 tipi di relazioni)
4. I documenti vengono inviati a **Zep Cloud**, che costruisce un grafo di conoscenza estraendo automaticamente entità e relazioni

### Fase 2 - Preparazione dell'Ambiente
1. Le entità estratte dal grafo vengono lette e filtrate
2. Ogni entità viene trasformata in un **profilo di agente AI** (personalità, bio, interessi, sentimenti) generato dal LLM e arricchito con i dati del grafo
3. Un LLM genera i parametri della simulazione: durata, frequenza di attività per agente, livelli di sentimento, eventi iniziali scatenanti

### Fase 3 - Simulazione Sociale
1. Viene lanciata una simulazione su **due piattaforme in parallelo**: Twitter e Reddit
2. Centinaia di agenti interagiscono: creano post, mettono like, commentano, condividono informazioni
3. Ogni azione è guidata dal ragionamento LLM dell'agente, basato sulla sua personalità
4. Il frontend mostra le azioni in tempo reale (feed live)
5. Opzionalmente, le azioni della simulazione vengono re-inserite nel grafo di conoscenza per arricchire la memoria

### Fase 4 - Generazione del Report
1. Un **Report Agent** (basato sul pattern ReACT con tool-calling) analizza i risultati della simulazione
2. Interroga il grafo di conoscenza tramite strumenti di retrieval (ricerca per insight, panoramica, ricerca rapida)
3. Produce un report strutturato per sezioni, visualizzato in streaming sul frontend

### Fase 5 - Interazione Profonda
1. **Modalità intervista**: si può chattare con qualsiasi singolo agente per approfondire il suo punto di vista
2. **Chat con il Report Agent**: si possono fare domande al report agent, che ha accesso agli strumenti di query del grafo per supportare le risposte

---

## Stack Tecnologico

### Backend (Python)
| Tecnologia | Scopo |
|---|---|
| Flask + Flask-CORS | API Web |
| OpenAI SDK | Client LLM unificato (qualsiasi API compatibile OpenAI) |
| Zep Cloud | Grafo di conoscenza, estrazione entità, GraphRAG |
| CAMEL-OASIS | Motore di simulazione social (Twitter + Reddit) |
| PyMuPDF | Estrazione testo da PDF |
| Pydantic | Validazione dati |
| `uv` | Package manager Python |

### Frontend (JavaScript)
| Tecnologia | Scopo |
|---|---|
| Vue 3 | Framework UI reattivo |
| Vue Router 4 | Routing client-side |
| Vue I18n | Internazionalizzazione (EN, IT, CN) |
| Vite 7 | Build tool e dev server |
| Axios | Client HTTP con retry |
| D3.js | Visualizzazione del grafo di conoscenza |

### DevOps
| Tecnologia | Scopo |
|---|---|
| Docker + Dockerfile | Deploy containerizzato |
| Docker Compose | Deploy con un solo comando |
| GitHub Actions | CI/CD per immagini Docker su GHCR |

### Servizi Esterni Richiesti
- **LLM API** (compatibile OpenAI, raccomandato: Alibaba Qwen-plus)
- **Zep Cloud** (servizio di grafo di conoscenza, tier gratuito disponibile)

---

## Struttura del Progetto

```
MiroFish-main/
├── backend/
│   ├── run.py                    # Punto di ingresso Flask (porta 5001)
│   ├── app/
│   │   ├── api/                  # Endpoint REST (graph, simulation, report)
│   │   ├── models/               # Modelli dati + gestione persistenza file
│   │   ├── services/             # Logica di business
│   │   │   ├── ontology_generator.py      # Generazione ontologia via LLM
│   │   │   ├── graph_builder.py           # Costruzione grafo Zep
│   │   │   ├── text_processor.py          # Preprocessamento e chunking testo
│   │   │   ├── oasis_profile_generator.py # Conversione entità → profili agente
│   │   │   ├── simulation_manager.py      # Gestione ciclo vita simulazione
│   │   │   ├── simulation_runner.py       # Esecuzione OASIS come subprocess
│   │   │   ├── report_agent.py            # Agente report con ReACT + tool-calling
│   │   │   └── zep_tools.py              # Strumenti retrieval per il Report Agent
│   │   └── utils/               # Utilità (LLM client, parser file, logging)
│   ├── scripts/                  # Script di simulazione + test
│   └── uploads/                  # Dati runtime (progetti, simulazioni, report)
├── frontend/
│   ├── src/
│   │   ├── views/                # Pagine principali (Home, Process, Simulation, Report, Interaction)
│   │   ├── components/           # Componenti UI (GraphPanel, Step 1-5, QuickTest, ecc.)
│   │   ├── api/                  # Chiamate API backend
│   │   ├── i18n/                 # Traduzioni (EN, IT)
│   │   └── config/               # Template quick test
│   └── vite.config.js            # Proxy /api → porta 5001
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/            # CI/CD
```

---

## Casi d'Uso

| Caso d'Uso | Descrizione |
|---|---|
| **Simulazione di opinione pubblica** | Esempio: evento nel campus dell'Università di Wuhan |
| **Previsione creativa** | Esempio: predire il finale perduto de "Il sogno della camera rossa" |
| **Reazione a un prodotto** | Template quick test: simulare come il mercato reagisce a un nuovo prodotto |
| **Impatto di una policy** | Template quick test: analizzare l'impatto di una nuova policy |
| **Campagna marketing** | Template quick test: simulare la reazione a una campagna pubblicitaria |
| **Valutazione prezzo** | Template quick test: testare l'accettabilità di un prezzo |
| **Sondaggio di opinione** | Template quick test: sondaggio su un tema specifico |

---

## Architettura Principale

```
Documenti utente → Estrazione testo → Ontologia via LLM → Grafo Zep
                                                              ↓
                                        Entità estratte ← Zep Cloud
                                                              ↓
                                        Profili agenti OASIS ← LLM
                                                              ↓
                                        Simulazione parallela (Twitter + Reddit)
                                                  ↓              ↓
                                              actions.jsonl   actions.jsonl
                                                  ↓
                                          Aggiornamento grafo (opzionale)
                                                  ↓
                                    Report Agent (ReACT + strumenti retrieval)
                                                  ↓
                                    Report previsione + Chat interattiva
```

### Pattern Architetturali Chiave
- **Task asincroni**: operazioni lunghe restituiscono un `task_id` e girano in background; il frontend polla per il progresso
- **IPC file-based**: comunicazione tra processo Flask e subprocess di simulazione tramite directory comandi/risposte
- **Singleton thread-safe**: `TaskManager` e `SimulationManager` usano pattern singleton
- **Persistenza su file**: progetti, simulazioni e report salvati come JSON/JSONL in `uploads/`

---

## Requisiti Hardware

MiroFish è un progetto puramente software. Non richiede GPU o hardware specialistico:
- Le chiamate LLM vanno a un API cloud esterna
- Il grafo di conoscenza è gestito da Zep Cloud
- La simulazione OASIS gira localmente ma orchestra chiamate LLM remote
- Il tutto è containerizzabile con Docker
