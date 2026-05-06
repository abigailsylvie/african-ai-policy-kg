"""
main.py
-------
Runs the full African AI Knowledge Graph pipeline:
  Step 1: Extract text from PDFs
  Step 2: Extract entities using Ollama
  Step 3: Load into Neo4j graph
  Step 4: Ready for GraphRAG queries

Usage:
  python main.py                    # run full pipeline
  python main.py --step extract     # only step 1
  python main.py --step entities    # only step 2
  python main.py --step load        # only step 3
  python main.py --suggest "Chad"   # suggest policy for a country
"""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

console = Console()


def run_pipeline(step: str = "all"):
    console.print(Panel(
        "[bold blue]African AI Policy Knowledge Graph[/bold blue]\n"
        "GraphRAG Pipeline for Policy Analysis & Suggestion",
        border_style="blue"
    ))

    if step in ("all", "extract"):
        console.print(Rule("[bold]Step 1: PDF Extraction[/bold]"))
        from src.extract import extract_all
        results = extract_all()
        if not results and step == "all":
            console.print("[red]No PDFs found — stopping pipeline.[/red]")
            console.print("Make sure PDFs are in data/policies/")
            sys.exit(1)

    if step in ("all", "entities"):
        console.print(Rule("[bold]Step 2: Entity Extraction (Ollama)[/bold]"))
        from src.entity_extractor import extract_all_entities
        extract_all_entities()

    if step in ("all", "load"):
        console.print(Rule("[bold]Step 3: Load into Neo4j[/bold]"))
        from src.graph_loader import load_all
        load_all()

    if step == "all":
        console.print(Rule())
        console.print("\n[bold green]✓ Pipeline complete![/bold green]")
        console.print("\nNow you can query the graph:")
        console.print("  [yellow]python main.py --suggest Chad[/yellow]")
        console.print("  [yellow]python main.py --suggest Mali[/yellow]")
        console.print("  [yellow]python main.py --list-missing[/yellow]")
        console.print("  [yellow]python main.py --summary[/yellow]")
        console.print("\nOr open Neo4j Browser at: [blue]http://localhost:7474[/blue]")
        console.print("  Cypher: [dim]MATCH (c:Country)-[r]->(n) RETURN c,r,n[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="African AI Knowledge Graph — GraphRAG Pipeline"
    )
    parser.add_argument(
        "--step",
        choices=["all", "extract", "entities", "load"],
        default="all",
        help="Which step to run (default: all)"
    )
    parser.add_argument(
        "--suggest",
        type=str,
        metavar="COUNTRY",
        help="Suggest an AI policy for a country without one"
    )
    parser.add_argument(
        "--list-missing",
        action="store_true",
        help="List all countries without AI policy"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show knowledge graph summary"
    )

    args = parser.parse_args()

    if args.suggest:
        from src.graphrag import GraphRAG
        rag = GraphRAG()
        rag.suggest_policy(args.suggest)
        rag.close()

    elif args.list_missing:
        from src.graphrag import GraphRAG
        rag = GraphRAG()
        missing = rag.get_countries_without_policy()
        console.print(f"\n[bold]{len(missing)} countries without AI policy:[/bold]")
        for c in missing:
            console.print(f"  • {c}")
        rag.close()

    elif args.summary:
        from src.graphrag import GraphRAG
        rag = GraphRAG()
        rag.show_graph_summary()
        rag.close()

    else:
        run_pipeline(step=args.step)


if __name__ == "__main__":
    main()