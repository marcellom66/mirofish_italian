<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="MiroFish Logo" width="75%"/>

Motore universale semplice di intelligenza collettiva, predici qualsiasi cosa
</br>
<em>A Simple and Universal Swarm Intelligence Engine, Predicting Anything</em>

<a href="https://www.shanda.com/" target="_blank"><img src="./static/image/shanda_logo.png" alt="Shanda" height="40"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/marcellom66/mirofish_italian?style=flat-square&color=DAA520)](https://github.com/marcellom66/mirofish_italian/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/marcellom66/mirofish_italian?style=flat-square)](https://github.com/marcellom66/mirofish_italian/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/marcellom66/mirofish_italian?style=flat-square)](https://github.com/marcellom66/mirofish_italian/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Italiano** | [English](./README-EN.md) | [中文](./README-CN.md) |

</div>

---

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

## Analisi Business Plan

MiroFish include una sezione dedicata all'**Analisi Business Plan**, accessibile dalla home page sotto i Quick Test. Permette di simulare scenari realistici intorno a un piano d'impresa tramite un wizard strutturato.

### Come funziona

1. Seleziona uno dei 4 template Business Plan dalla home page
2. **Step 1 — Profilo Aziendale**: compila i campi strutturati:
   - Settore, fase aziendale (Startup / Crescita / Matura / Exit)
   - Mercato target, budget stimato, principali competitor
   - KPI prioritari (Fatturato, Quota Mercato, Retention, CAC, NPS, EBITDA)
   - Aree di rischio (Mercato, Finanziario, Operativo, Regolatorio, Competitivo)
   - Stakeholder da simulare (Investitori/VC, Clienti B2B, Clienti B2C, Competitor, Dipendenti, Media)
   - Orizzonte temporale (6 mesi / 1 anno / 3 anni / 5 anni)
3. **Step 2 — Scenario**: revisiona e personalizza il prompt di simulazione auto-generato, allega documenti opzionali (PDF, MD, TXT)
4. La pipeline completa (grafo → simulazione → report) viene eseguita con il contesto del business plan
5. Il Report Agent genera sezioni focalizzate su: reazioni degli stakeholder, impatto sui KPI, valutazione dei rischi, raccomandazioni strategiche

### Template disponibili

| Template | Descrizione |
|---|---|
| 📊 **Analisi Multi-Scenario** | Simula scenari ottimistici, realistici e pessimistici del piano |
| 📈 **Evoluzione nel Tempo** | Simula le reazioni nelle fasi di lancio, crescita e maturità |
| 🎯 **Analisi Competitiva** | Simula le reazioni di competitor, investitori e clienti target |
| 🏢 **Analisi Completa** | Analisi completa con matrice di rischio e raccomandazioni strategiche |

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
| **Analisi business plan** | Sezione dedicata: analisi multi-scenario, evoluzione, competitiva o completa |

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

## Avvio Rapido

1. Configura variabili in `.env` a partire da `.env.example`.
2. Installa dipendenze:

```bash
npm run setup
npm run setup:backend
```

3. Avvia frontend + backend:

```bash
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

---

## Requisiti Hardware

MiroFish è un progetto puramente software. Non richiede GPU o hardware specialistico:
- Le chiamate LLM vanno a un API cloud esterna
- Il grafo di conoscenza è gestito da Zep Cloud
- La simulazione OASIS gira localmente ma orchestra chiamate LLM remote
- Il tutto è containerizzabile con Docker

---

## Licenza

Questo progetto è distribuito sotto licenza **GNU Affero General Public License v3.0 (AGPL-3.0)**. Vedere il file [LICENSE](./LICENSE) per i dettagli.

Progetto originale: [666ghj/MiroFish](https://github.com/666ghj/MiroFish)
