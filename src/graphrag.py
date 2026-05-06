"""
graphrag.py
-----------
GraphRAG query layer:
  1. Retrieve context from Neo4j graph
  2. Feed that context to Groq LLM (free, fast, cloud)
  3. Generate AI policy suggestions for countries without one
"""

import os
import argparse
from neo4j import GraphDatabase
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
console = Console()

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GROQ_MODEL     = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)


class GraphRAG:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def get_countries_with_policy(self):
        with self.driver.session() as session:
            result = session.run("MATCH (c:Country {has_policy: true}) RETURN c.name AS name")
            return [r["name"] for r in result]

    def get_countries_without_policy(self):
        with self.driver.session() as session:
            result = session.run("MATCH (c:Country {has_policy: false}) RETURN c.name AS name ORDER BY c.name")
            return [r["name"] for r in result]

    def get_country_profile(self, country):
        with self.driver.session() as session:
            pillars = [r["name"] for r in session.run(
                "MATCH (:Country {name:$c})-[:HAS_PILLAR]->(p) RETURN p.name AS name", c=country)]
            sectors = [r["name"] for r in session.run(
                "MATCH (:Country {name:$c})-[:TARGETS_SECTOR]->(s) RETURN s.name AS name", c=country)]
            institutions = [r["name"] for r in session.run(
                "MATCH (:Country {name:$c})-[:HAS_INSTITUTION]->(i) RETURN i.name AS name", c=country)]
            goals = [r["name"] for r in session.run(
                "MATCH (:Country {name:$c})-[:HAS_GOAL]->(g) RETURN g.name AS name", c=country)]
            risks = [r["name"] for r in session.run(
                "MATCH (:Country {name:$c})-[:FACES_RISK]->(r) RETURN r.name AS name", c=country)]
        return {
            "country": country,
            "pillars": pillars,
            "sectors": sectors,
            "institutions": institutions,
            "goals": goals,
            "risks": risks,
        }

    def get_most_common_patterns(self):
        with self.driver.session() as session:
            top_pillars = [r["name"] for r in session.run("""
                MATCH (:Country {has_policy:true})-[:HAS_PILLAR]->(p)
                RETURN p.name AS name, count(*) AS freq
                ORDER BY freq DESC LIMIT 5
            """)]
            top_sectors = [r["name"] for r in session.run("""
                MATCH (:Country {has_policy:true})-[:TARGETS_SECTOR]->(s)
                RETURN s.name AS name, count(*) AS freq
                ORDER BY freq DESC LIMIT 5
            """)]
            top_risks = [r["name"] for r in session.run("""
                MATCH (:Country {has_policy:true})-[:FACES_RISK]->(r)
                RETURN r.name AS name, count(*) AS freq
                ORDER BY freq DESC LIMIT 5
            """)]
        return {
            "top_pillars": top_pillars,
            "top_sectors": top_sectors,
            "top_risks": top_risks,
        }

    def build_context(self):
        """Build a short, token-efficient context from the graph."""
        countries = self.get_countries_with_policy()
        profiles = [self.get_country_profile(c) for c in countries]
        patterns = self.get_most_common_patterns()

        lines = ["=== EXISTING AFRICAN AI POLICIES ===\n"]
        for p in profiles:
            lines.append(f"Country: {p['country']}")
            lines.append(f"  Pillars: {', '.join(p['pillars'][:4]) or 'N/A'}")
            lines.append(f"  Sectors: {', '.join(p['sectors'][:3]) or 'N/A'}")
            lines.append(f"  Institutions: {', '.join(p['institutions'][:2]) or 'N/A'}")
            lines.append(f"  Goals: {', '.join(p['goals'][:2]) or 'N/A'}")
            lines.append(f"  Risks: {', '.join(p['risks'][:2]) or 'N/A'}")
            lines.append("")

        lines.append("=== COMMON PATTERNS ===")
        lines.append(f"  Top pillars: {', '.join(patterns['top_pillars'])}")
        lines.append(f"  Top sectors: {', '.join(patterns['top_sectors'])}")
        lines.append(f"  Top risks: {', '.join(patterns['top_risks'])}")

        return "\n".join(lines)

    def suggest_policy(self, target_country):
        console.print(f"\n[bold blue]Generating AI policy suggestion for: {target_country}[/bold blue]")
        console.print("[dim]Retrieving graph context...[/dim]")

        context = self.build_context()

        prompt = f"""You are an expert AI policy advisor for Africa.
Based on existing African AI policies below, suggest a policy framework for {target_country}.

{context}

Create a practical AI policy for {target_country} with:
1. CONTEXT: Brief context about {target_country} and AI readiness
2. RECOMMENDED PILLARS: 4-5 key strategic pillars
3. PRIORITY SECTORS: Top 3 sectors to target first
4. SUGGESTED INSTITUTIONS: Governance bodies to create
5. KEY GOALS (2025-2030): 3 measurable goals
6. RISKS TO ADDRESS: Top 2 risks and mitigation
7. LEARN FROM: Which African country to model and why

Be specific, practical, and realistic for the African context."""

        console.print("[dim]Querying Groq...[/dim]\n")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        suggestion = response.choices[0].message.content

        console.print(Panel(
            suggestion,
            title=f"[bold green]AI Policy Suggestion for {target_country}[/bold green]",
            border_style="green"
        ))

        out_path = f"data/suggestions_{target_country.lower().replace(' ', '_')}.txt"
        with open(out_path, "w") as f:
            f.write(f"AI Policy Suggestion for {target_country}\n")
            f.write("=" * 60 + "\n\n")
            f.write(suggestion)
        console.print(f"\n[dim]Saved to {out_path}[/dim]")

        return suggestion

    def show_graph_summary(self):
        countries_with = self.get_countries_with_policy()
        countries_without = self.get_countries_without_policy()
        patterns = self.get_most_common_patterns()

        console.print(Panel(
            f"[bold]Countries WITH AI Policy:[/bold] {', '.join(countries_with)}\n\n"
            f"[bold]Countries WITHOUT AI Policy:[/bold] {len(countries_without)} countries\n\n"
            f"[bold]Top Policy Pillars:[/bold] {', '.join(patterns['top_pillars'])}\n"
            f"[bold]Top Sectors:[/bold] {', '.join(patterns['top_sectors'])}\n"
            f"[bold]Top Risks:[/bold] {', '.join(patterns['top_risks'])}",
            title="[bold blue]African AI Knowledge Graph Summary[/bold blue]",
            border_style="blue"
        ))


def main():
    parser = argparse.ArgumentParser(description="GraphRAG for African AI Policies")
    parser.add_argument("--country", type=str, help="Suggest AI policy for this country")
    parser.add_argument("--list-missing", action="store_true", help="List countries without AI policy")
    parser.add_argument("--summary", action="store_true", help="Show graph summary")
    args = parser.parse_args()

    rag = GraphRAG()

    if args.list_missing:
        missing = rag.get_countries_without_policy()
        console.print("\n[bold]Countries without AI policy:[/bold]")
        for c in missing:
            console.print(f"  • {c}")
    elif args.summary:
        rag.show_graph_summary()
    elif args.country:
        rag.suggest_policy(args.country)
    else:
        rag.show_graph_summary()

    rag.close()


if __name__ == "__main__":
    main()