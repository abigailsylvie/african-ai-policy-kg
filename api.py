"""
api.py
------
FastAPI REST API for the African AI Knowledge Graph.

Run with:
  uvicorn api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.graphrag import GraphRAG

# ── App setup ────────────────────────────────────────────────────
app = FastAPI(
    title="African AI Policy Knowledge Graph API",
    description="GraphRAG-powered API that maps AI policies across Africa and suggests frameworks for countries without one.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Response models ──────────────────────────────────────────────
class CountryProfile(BaseModel):
    country: str
    pillars: list[str]
    sectors: list[str]
    institutions: list[str]
    goals: list[str]
    risks: list[str]

class SuggestionResponse(BaseModel):
    country: str
    suggestion: str
    saved_to: str

class SummaryResponse(BaseModel):
    countries_with_policy: list[str]
    countries_without_policy: list[str]
    total_without_policy: int
    top_pillars: list[str]
    top_sectors: list[str]
    top_risks: list[str]

# ── Routes ───────────────────────────────────────────────────────

@app.get("/", tags=["General"])
def root():
    return {
        "project": "African AI Policy Knowledge Graph",
        "description": "GraphRAG API to map and suggest AI policies across Africa",
        "endpoints": {
            "summary":          "GET  /summary",
            "countries_with":   "GET  /countries/with-policy",
            "countries_missing":"GET  /countries/missing",
            "country_profile":  "GET  /country/{name}",
            "suggest_policy":   "POST /suggest/{country}",
        }
    }


@app.get("/summary", response_model=SummaryResponse, tags=["Graph"])
def get_summary():
    """Get an overview of the entire knowledge graph."""
    rag = GraphRAG()
    try:
        countries_with    = rag.get_countries_with_policy()
        countries_without = rag.get_countries_without_policy()
        patterns          = rag.get_most_common_patterns()
        return SummaryResponse(
            countries_with_policy=countries_with,
            countries_without_policy=countries_without,
            total_without_policy=len(countries_without),
            top_pillars=patterns["top_pillars"],
            top_sectors=patterns["top_sectors"],
            top_risks=patterns["top_risks"],
        )
    finally:
        rag.close()


@app.get("/countries/with-policy", tags=["Countries"])
def countries_with_policy():
    """List all African countries that have an AI policy."""
    rag = GraphRAG()
    try:
        countries = rag.get_countries_with_policy()
        return {"count": len(countries), "countries": countries}
    finally:
        rag.close()


@app.get("/countries/missing", tags=["Countries"])
def countries_missing_policy():
    """List all African countries that do NOT have an AI policy."""
    rag = GraphRAG()
    try:
        countries = rag.get_countries_without_policy()
        return {"count": len(countries), "countries": countries}
    finally:
        rag.close()


@app.get("/country/{name}", response_model=CountryProfile, tags=["Countries"])
def get_country_profile(name: str):
    """
    Get the full knowledge graph profile for a specific country.
    Example: /country/Kenya
    """
    rag = GraphRAG()
    try:
        countries = rag.get_countries_with_policy()
        # Case-insensitive match
        matched = next((c for c in countries if c.lower() == name.lower()), None)
        if not matched:
            raise HTTPException(
                status_code=404,
                detail=f"Country '{name}' not found or has no AI policy in the graph. "
                       f"Available: {', '.join(countries)}"
            )
        profile = rag.get_country_profile(matched)
        return CountryProfile(**profile)
    finally:
        rag.close()


@app.post("/suggest/{country}", response_model=SuggestionResponse, tags=["GraphRAG"])
def suggest_policy(country: str):
    """
    Generate an AI policy suggestion for a country using GraphRAG.
    Pulls context from the knowledge graph and uses Groq LLM to generate
    a tailored policy framework.

    Example: POST /suggest/Chad
    """
    rag = GraphRAG()
    try:
        suggestion = rag.suggest_policy(country)
        saved_to = f"data/suggestions_{country.lower().replace(' ', '_')}.txt"
        return SuggestionResponse(
            country=country,
            suggestion=suggestion,
            saved_to=saved_to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        rag.close()
