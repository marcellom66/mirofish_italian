<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="MiroFish Logo" width="75%"/>

<a href="https://trendshift.io/repositories/16144" target="_blank"><img src="https://trendshift.io/api/badge/repositories/16144" alt="666ghj%2FMiroFish | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

Simple and universal collective intelligence engine, predict anything
</br>
<em>A Simple and Universal Swarm Intelligence Engine, Predicting Anything</em>
</br>
<em>Motore universale semplice di intelligenza collettiva, predici qualsiasi cosa</em>

<a href="https://www.shanda.com/" target="_blank"><img src="./static/image/shanda_logo.png" alt="666ghj%2MiroFish | Shanda" height="40"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/666ghj/MiroFish?style=flat-square&color=DAA520)](https://github.com/666ghj/MiroFish/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/666ghj/MiroFish)

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white)](http://discord.gg/ePf5aPaHnA)
[![X](https://img.shields.io/badge/X-Follow-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/mirofish_ai)
[![Instagram](https://img.shields.io/badge/Instagram-Follow-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/mirofish_ai/)

[Italiano](./README.md) | **English** | [中文](./README-CN.md) |

</div>

## ⚡ Overview

**MiroFish** is a next-generation AI prediction engine powered by multi-agent technology. By extracting seed information from the real world (such as breaking news, policy drafts, or financial signals), it automatically constructs a high-fidelity parallel digital world. Within this space, thousands of intelligent agents with independent personalities, long-term memory, and behavioral logic freely interact and undergo social evolution. You can inject variables dynamically from a "God's-eye view" to precisely deduce future trajectories — **rehearse the future in a digital sandbox, and win decisions after countless simulations**.

> You only need to: Upload seed materials (data analysis reports or interesting novel stories) and describe your prediction requirements in natural language</br>
> MiroFish will return: A detailed prediction report and a deeply interactive high-fidelity digital world

### Our Vision

MiroFish is dedicated to creating a swarm intelligence mirror that maps reality. By capturing the collective emergence triggered by individual interactions, we break through the limitations of traditional prediction:

- **At the Macro Level**: We are a rehearsal laboratory for decision-makers, allowing policies and public relations to be tested at zero risk
- **At the Micro Level**: We are a creative sandbox for individual users — whether deducing novel endings or exploring imaginative scenarios, everything can be fun, playful, and accessible

From serious predictions to playful simulations, we let every "what if" see its outcome, making it possible to predict anything.

## 🌐 Live Demo

Welcome to visit our online demo environment and experience a prediction simulation on trending public opinion events we've prepared for you: [mirofish-live-demo](https://666ghj.github.io/mirofish-demo/)

## 📸 Screenshots

Screenshots are available in the online demo and in project release materials.

## 🎬 Demo Videos

### 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction

<div align="center">
<a href="https://www.bilibili.com/video/BV1VYBsBHEMY/" target="_blank">Open demo video</a>

Click the image to watch the complete demo video for prediction using BettaFish-generated "Wuhan University Public Opinion Report"
</div>

### 2. Dream of the Red Chamber Lost Ending Simulation

<div align="center">
<a href="https://www.bilibili.com/video/BV1cPk3BBExq" target="_blank">Open demo video</a>

Click the image to watch MiroFish's deep prediction of the lost ending based on hundreds of thousands of words from the first 80 chapters of "Dream of the Red Chamber"
</div>

> **Financial Prediction**, **Political News Prediction** and more examples coming soon...

## 📊 Business Plan Analysis

MiroFish includes a dedicated **Business Plan Analysis** section on the home page, alongside the Quick Test templates. It enables structured scenario simulation for business plans through a guided two-step wizard.

### How It Works

1. Select one of the 4 Business Plan templates from the home page
2. **Step 1 — Company Profile**: fill in structured fields (or import directly from an Excel file):
   - Sector, business phase (Startup / Growth / Mature / Exit)
   - Target market, estimated budget, main competitors
   - Priority KPIs (Revenue, Market Share, Retention, CAC, NPS, EBITDA)
   - Risk areas (Market, Financial, Operational, Regulatory, Competitive)
   - Stakeholders to simulate (Investors/VC, B2B Customers, B2C Customers, Competitors, Employees, Media)
   - Forecast horizon (6 months / 1 year / 3 years / 5 years)
3. **Step 2 — Scenario**: review and edit the auto-generated simulation prompt, optionally attach documents (PDF, MD, TXT)
4. The full pipeline (graph → simulation → report) runs with your business plan context
5. The Report Agent generates sections focused on: stakeholder reactions, KPI impact, risk evaluation, strategic recommendations

### Excel Import (.xlsx)

The wizard supports direct import from a structured Excel file. The file can contain up to **5 sheets**:

| Sheet | Columns | Description |
|---|---|---|
| `Company Profile` | Campo \| Valore | Company profile fields (company_name, sector, phase, competitors, kpis, etc.) |
| `Financial Data` | Indicatore \| Valore \| Unità | Key financial data (revenue, EBITDA, operating margin, etc.) |
| `People & Roles` | Name \| Role \| Group \| Organization \| Notes | Named stakeholders with role and organization |
| `Competitor Brands` | Brand \| Positioning \| PriceBand \| CoreMarkets \| Notes | Detailed competitor profiles |
| `Node Relationships` | Source \| SourceType \| Relationship \| Target \| TargetType \| Description | **Explicit graph node relationships** |

#### The Node Relationships Sheet — the heart of the knowledge graph

The `Node Relationships` sheet is the most important component for analysis quality. It defines **explicit relationships between actors** in the business plan. These are embedded into the seed file text that Zep Cloud processes to build the knowledge graph, allowing precise semantic edges to be extracted rather than relying solely on automatic inference.

**Row format:**

```
Source          | SourceType   | Relationship    | Target              | TargetType   | Description
Mario Rossi     | Customer     | BUYS_FROM       | Barilla             | Company      | Mario Rossi, Head of Procurement...
Barilla         | Company      | COMPETES_WITH   | De Cecco            | Company      | Barilla directly competes with...
Paolo Verdi     | Journalist   | COVERS          | Barilla             | Company      | Paolo Verdi covers Barilla's ESG strategy...
Elena Neri      | Investor     | EVALUATES       | Barilla             | Company      | Elena Neri monitors Barilla's EBITDA growth...
Luca Moretti    | Supplier     | SUPPLIES_TO     | Barilla             | Company      | Luca Moretti supplies durum wheat to...
```

**Supported relationship types** (examples):
- `BUYS_FROM` — B2B/B2C customers toward the company
- `COVERS` — journalists and media toward the company
- `EVALUATES` — investors toward the company
- `SUPPLIES_TO` — suppliers toward the company
- `DISTRIBUTES_FOR` — distributors toward the company
- `COMPETES_WITH` — competitors toward the company (and vice versa)
- `WORKS_FOR` — people toward their respective organizations

**How it works technically**: at launch time, the wizard builds a `.txt` seed file containing the template prefix (company context, stakeholders, scenarios) plus the scenario text. If the `Node Relationships` sheet is present in the imported Excel, the relationships are converted into narrative sentences and **appended to the seed file** under a `KEY ACTOR RELATIONSHIPS` section. Zep Cloud processes this text and automatically populates the graph with nodes and edges corresponding to real actors and their relationships.

#### Included demo file

The repository includes a pre-filled sample Excel file:

```
frontend/public/demo/barilla_business_plan.xlsx
```

This file models a real-world case — **Barilla S.p.A.** — with 25 predefined relationships between the company, competitors, B2B/B2C customers, suppliers, distributors, media, and investors. It can be used directly as a reference template for creating custom files.

### Available Templates

| Template | Description |
|---|---|
| 📊 **Multi-Scenario Analysis** | Simulate optimistic, realistic and pessimistic outcomes |
| 📈 **Evolution Over Time** | Simulate reactions across launch, growth and maturity phases |
| 🎯 **Competitive Analysis** | Simulate competitor, investor and customer reactions |
| 🏢 **Full Business Plan Analysis** | Comprehensive analysis with risk matrix and strategic recommendations |

## 🔄 Workflow

1. **Graph Building**: Seed extraction & Individual/collective memory injection & GraphRAG construction
2. **Environment Setup**: Entity relationship extraction & Persona generation & Agent configuration injection
3. **Simulation**: Dual-platform parallel simulation & Auto-parse prediction requirements & Dynamic temporal memory updates
4. **Report Generation**: ReportAgent with rich toolset for deep interaction with post-simulation environment
5. **Deep Interaction**: Chat with any agent in the simulated world & Interact with ReportAgent

## 🚀 Quick Start

### Option 1: Source Code Deployment (Recommended)

#### Prerequisites

| Tool | Version | Description | Check Installation |
|------|---------|-------------|-------------------|
| **Node.js** | 18+ | Frontend runtime, includes npm | `node -v` |
| **Python** | ≥3.11, ≤3.12 | Backend runtime | `python --version` |
| **uv** | Latest | Python package manager | `uv --version` |

#### 1. Configure Environment Variables

```bash
# Copy the example configuration file
cp .env.example .env

# Edit the .env file and fill in the required API keys
```

**Required Environment Variables:**

```env
# LLM API Configuration (supports any LLM API with OpenAI SDK format)
# Recommended: Alibaba Qwen-plus model via Bailian Platform: https://bailian.console.aliyun.com/
# High consumption, try simulations with fewer than 40 rounds first
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep Cloud Configuration
# Free monthly quota is sufficient for simple usage: https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key
```

#### 2. Install Dependencies

```bash
# One-click installation of all dependencies (root + frontend + backend)
npm run setup:all
```

Or install step by step:

```bash
# Install Node dependencies (root + frontend)
npm run setup

# Install Python dependencies (backend, auto-creates virtual environment)
npm run setup:backend
```

#### 3. Start Services

```bash
# Start both frontend and backend (run from project root)
npm run dev
```

**Service URLs:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

**Start Individually:**

```bash
npm run backend   # Start backend only
npm run frontend  # Start frontend only
```

### Option 2: Docker Deployment

```bash
# 1. Configure environment variables (same as source deployment)
cp .env.example .env

# 2. Pull image and start
docker compose up -d
```

Reads `.env` from root directory by default, maps ports `3000 (frontend) / 5001 (backend)`

> Mirror address for faster pulling is provided as comments in `docker-compose.yml`, replace if needed.

## 📬 Join the Conversation

<div align="center">
QQ group image is available in the repository static assets.
</div>

&nbsp;

The MiroFish team is recruiting full-time/internship positions. If you're interested in multi-agent simulation and LLM applications, feel free to send your resume to: **mirofish@shanda.com**

## 📄 Acknowledgments

**MiroFish has received strategic support and incubation from Shanda Group!**

MiroFish's simulation engine is powered by **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)**, We sincerely thank the CAMEL-AI team for their open-source contributions!

## 📈 Project Statistics

<a href="https://www.star-history.com/#666ghj/MiroFish&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&legend=top-left" />
 </picture>
</a>