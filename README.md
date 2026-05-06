# 🌍 African AI Policy Knowledge Graph

> *What if we could use existing African AI policies to help countries that don't have one yet?*

That's exactly what this project does.

---

## The Problem

Africa has 54 countries. Only a handful have a national AI policy — Kenya, Rwanda, Ghana, Zambia, and a few others. The rest? Nothing. No roadmap, no governance framework, no strategy.

This is a problem because AI is already here, and countries without policies are navigating it blind.

---

## What This Project Does

This project builds a **knowledge graph** from real African AI policy documents (PDFs), extracts key information from them, stores everything in a graph database, and then uses **GraphRAG** (Graph + AI) to suggest tailored AI policy frameworks for countries that don't have one.

You ask: *"What should Chad's AI policy look like?"*

The system looks at what Kenya, Rwanda, Ghana, and Zambia did, finds patterns, and generates a practical, country-specific suggestion.

---

## How It Works

```
PDF Policies (Kenya, Rwanda, Ghana, Zambia, African Union)
        ↓
Extract text with pdfplumber
        ↓
Extract entities with Groq AI (pillars, sectors, goals, risks, institutions)
        ↓
Store in Neo4j Knowledge Graph
        ↓
GraphRAG: query the graph + generate suggestions with LLM
        ↓
FastAPI REST API to access everything
```

---

## Project Structure

```
african-ai-kg/
├── data/
│   ├── policies/          ← Put your PDF files here
│   ├── extracted/         ← Extracted text (auto-generated)
│   └── entities/          ← Extracted entities (auto-generated)
├── src/
│   ├── extract.py         ← Step 1: PDF → text
│   ├── entity_extractor.py← Step 2: text → entities (Groq AI)
│   ├── graph_loader.py    ← Step 3: entities → Neo4j graph
│   └── graphrag.py        ← Step 4: graph + LLM = suggestions
├── api.py                 ← FastAPI REST API
├── main.py                ← Run the full pipeline
├── requirements.txt
└── .env.example           ← Environment variables template
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/african-ai-policy-kg.git
cd african-ai-policy-kg
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate       # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

### 5. Download the policy PDFs

| Country | Source |
|---|---|
| Kenya | https://ict.go.ke/sites/default/files/2025-03/Kenya%20AI%20Strategy%202025%20-%202030.pdf |
| Rwanda | https://www.minict.gov.rw/index.php?eID=dumpFile&t=f&f=67550 |
| Ghana | https://www.africadataprotection.org/Ghana-AI-Strat.pdf |
| Zambia | https://www.mots.gov.zm/wp-content/uploads/2025/02/Zambia-Ai-Strategy-Book-option-2.pdf |
| African Union | https://au.int/sites/default/files/documents/44004-doc-EN-_Continental_AI_Strategy_July_2024.pdf |

Place them in `data/policies/`.

### 6. Run the pipeline

```bash
python main.py
```

This runs all 3 steps: extract → entities → load into graph.

### 7. Start the API

```bash
uvicorn api:app --reload
```

Open `http://localhost:8000/docs` to explore the API.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome + project info |
| GET | `/summary` | Knowledge graph overview |
| GET | `/countries/with-policy` | Countries that have AI policies |
| GET | `/countries/missing` | Countries without AI policies |
| GET | `/country/{name}` | Profile of a specific country |
| POST | `/suggest/{country}` | Generate AI policy suggestion |

### Example

```bash
# Suggest a policy for Chad
curl -X POST http://localhost:8000/suggest/Chad
```

---

## Requirements

- Python 3.10+
- [Neo4j AuraDB](https://console.neo4j.io) — free tier works
- [Groq API key](https://console.groq.com) — free tier works

---

## What's Next

- [ ] Add more country policies (Egypt, Nigeria, Senegal, Ethiopia)
- [ ] Build a frontend dashboard with a map of Africa
- [ ] Export suggestions as PDF reports
- [ ] Add similarity scoring between countries

---

## Why This Matters

The African Union's Continental AI Strategy (2025–2030) calls for every African country to have a national AI framework. This tool is built to support exactly that — using the knowledge from countries that are ahead to help countries that are just getting started.

---

## Built With

- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF text extraction
- [Groq](https://groq.com) — Fast, free LLM API
- [Neo4j](https://neo4j.com) — Graph database
- [FastAPI](https://fastapi.tiangolo.com) — REST API framework

---

*Built to support AI governance across Africa. 🌍*
