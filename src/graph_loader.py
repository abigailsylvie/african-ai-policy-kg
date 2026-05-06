"""
graph_loader.py
---------------
Loads extracted entities into Neo4j as a knowledge graph.

Graph schema:
  (Country)-[:HAS_PILLAR]->(PolicyPillar)
  (Country)-[:TARGETS_SECTOR]->(Sector)
  (Country)-[:HAS_GOAL]->(Goal)
  (Country)-[:MANAGED_BY]->(Institution)
  (PolicyPillar)-[:ADDRESSES_RISK]->(Risk)
  (Country)-[:SIMILAR_TO]->(Country)   ← computed later by GraphRAG
"""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

ENTITIES_DIR = Path("data/entities")

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class GraphLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        console.print(f"[green]✓ Connected to Neo4j at {NEO4J_URI}[/green]")

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Wipe all nodes and relationships (fresh start)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        console.print("[yellow]⚠ Database cleared[/yellow]")

    def create_constraints(self):
        """Create uniqueness constraints for clean merging."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:PolicyPillar) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Institution) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Goal) REQUIRE g.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Risk) REQUIRE r.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for c in constraints:
                session.run(c)
        console.print("[green]✓ Constraints created[/green]")

    def load_country(self, data: dict):
        """Load a single country's entities into Neo4j."""
        country = data.get("country", "Unknown")
        if not country:
            return

        with self.driver.session() as session:

            # Country node — mark as "has_policy" = True
            session.run(
                "MERGE (c:Country {name: $name}) SET c.has_policy = true",
                name=country
            )

            # PolicyPillar nodes + relationship
            for pillar in data.get("policy_pillars", []):
                if pillar:
                    session.run("""
                        MERGE (p:PolicyPillar {name: $pillar})
                        WITH p
                        MATCH (c:Country {name: $country})
                        MERGE (c)-[:HAS_PILLAR]->(p)
                    """, pillar=pillar, country=country)

            # Sector nodes + relationship
            for sector in data.get("sectors", []):
                if sector:
                    session.run("""
                        MERGE (s:Sector {name: $sector})
                        WITH s
                        MATCH (c:Country {name: $country})
                        MERGE (c)-[:TARGETS_SECTOR]->(s)
                    """, sector=sector, country=country)

            # Institution nodes + relationship
            for inst in data.get("institutions", []):
                if inst:
                    session.run("""
                        MERGE (i:Institution {name: $inst})
                        WITH i
                        MATCH (c:Country {name: $country})
                        MERGE (c)-[:HAS_INSTITUTION]->(i)
                    """, inst=inst, country=country)

            # Goal nodes + relationship
            for goal in data.get("goals", []):
                if goal:
                    session.run("""
                        MERGE (g:Goal {name: $goal})
                        WITH g
                        MATCH (c:Country {name: $country})
                        MERGE (c)-[:HAS_GOAL]->(g)
                    """, goal=goal, country=country)

            # Risk nodes + relationship
            for risk in data.get("risks", []):
                if risk:
                    session.run("""
                        MERGE (r:Risk {name: $risk})
                        WITH r
                        MATCH (c:Country {name: $country})
                        MERGE (c)-[:FACES_RISK]->(r)
                    """, risk=risk, country=country)

        console.print(f"  [green]✓[/green] {country} loaded into graph")

    def add_countries_without_policy(self):
        """
        Add African countries that have NO AI policy yet.
        These are the countries we want to suggest policies for.
        """
        no_policy_countries = [
            # Central Africa
            "Chad", "Central African Republic", "Congo", "Cameroon", "Gabon",
            # West Africa
            "Mali", "Niger", "Burkina Faso", "Guinea", "Sierra Leone", "Liberia",
            "Togo", "Benin", "Gambia", "Guinea-Bissau", "Cape Verde",
            # East Africa
            "Somalia", "Eritrea", "Djibouti", "South Sudan", "Burundi",
            "Comoros", "Madagascar",
            # Southern Africa
            "Malawi", "Mozambique", "Angola", "Lesotho", "Eswatini",
            # North Africa
            "Libya", "Sudan",
        ]
        with self.driver.session() as session:
            for country in no_policy_countries:
                session.run(
                    "MERGE (c:Country {name: $name}) SET c.has_policy = false",
                    name=country
                )
        console.print(f"[green]✓ Added {len(no_policy_countries)} countries without AI policy[/green]")

    def compute_similarity(self):
        """
        Create SIMILAR_TO relationships between countries based on
        shared sectors and pillars (foundation for GraphRAG suggestions).
        """
        query = """
        MATCH (c1:Country {has_policy: true})-[:TARGETS_SECTOR]->(s:Sector)
              <-[:TARGETS_SECTOR]-(c2:Country {has_policy: true})
        WHERE c1 <> c2
        WITH c1, c2, count(s) AS shared_sectors
        WHERE shared_sectors > 1
        MERGE (c1)-[r:SIMILAR_TO]-(c2)
        SET r.shared_sectors = shared_sectors
        """
        with self.driver.session() as session:
            session.run(query)
        console.print("[green]✓ SIMILAR_TO relationships computed[/green]")

    def get_stats(self) -> dict:
        """Return node counts for each label."""
        labels = ["Country", "PolicyPillar", "Sector", "Institution", "Goal", "Risk"]
        stats = {}
        with self.driver.session() as session:
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                stats[label] = result.single()["count"]
        return stats


def load_all():
    """Main function: load all entity JSON files into Neo4j."""
    entity_files = list(ENTITIES_DIR.glob("*_entities.json"))

    if not entity_files:
        console.print("[red]No entity files found. Run entity_extractor.py first![/red]")
        return

    loader = GraphLoader()
    loader.clear_database()
    loader.create_constraints()

    console.print(f"\n[bold blue]Loading {len(entity_files)} country graphs...[/bold blue]\n")

    for entity_file in entity_files:
        data = json.loads(entity_file.read_text(encoding="utf-8"))
        loader.load_country(data)

    loader.add_countries_without_policy()
    loader.compute_similarity()

    stats = loader.get_stats()
    loader.close()

    console.print("\n[bold green]Graph loaded! Summary:[/bold green]")
    for label, count in stats.items():
        console.print(f"  {label:15} → {count} nodes")


if __name__ == "__main__":
    load_all()