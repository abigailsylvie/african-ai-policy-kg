import json
import re
import os
from pathlib import Path
from tqdm import tqdm
from rich.console import Console
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
console = Console()

OUT_DIR      = Path("data/extracted")
ENTITIES_DIR = Path("data/entities")
ENTITIES_DIR.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL = "llama-3.1-8b-instant"
CHUNK_SIZE = 3000

EXTRACTION_PROMPT = """
You are an AI policy analyst. Extract structured information from this African AI policy document excerpt.

Return ONLY valid JSON with this exact structure (no extra text, no markdown, no code fences):
{{
  "country": "string",
  "policy_pillars": ["list of main strategic pillars or themes"],
  "institutions": ["list of government bodies, agencies, or councils mentioned"],
  "goals": ["list of specific goals or targets mentioned"],
  "sectors": ["list of sectors targeted (e.g. Healthcare, Agriculture, Education)"],
  "risks": ["list of risks or challenges mentioned"],
  "relationships": [
    {{"from": "entity_name", "type": "RELATIONSHIP_TYPE", "to": "entity_name"}}
  ]
}}

Relationship types:
- HAS_PILLAR, TARGETS_SECTOR, MANAGED_BY, ADDRESSES_RISK, HAS_GOAL

Document excerpt (country: {country}):
---
{text}
---

Return only the JSON object:
"""

def chunk_text(text, size=CHUNK_SIZE):
    words = text.split()
    chunks = []
    step = size // 2
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + size])
        if chunk:
            chunks.append(chunk)
        if i + size >= len(words):
            break
    return chunks

def parse_llm_response(response_text):
    cleaned = re.sub(r"```json|```", "", response_text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None

def merge_entities(entities_list):
    merged = {
        "country": "",
        "policy_pillars": set(),
        "institutions": set(),
        "goals": set(),
        "sectors": set(),
        "risks": set(),
        "relationships": [],
    }
    seen_rels = set()
    for e in entities_list:
        if not merged["country"] and e.get("country"):
            merged["country"] = e["country"]
        for key in ["policy_pillars", "institutions", "goals", "sectors", "risks"]:
            merged[key].update(e.get(key, []))
        for rel in e.get("relationships", []):
            rel_key = (rel.get("from"), rel.get("type"), rel.get("to"))
            if rel_key not in seen_rels:
                merged["relationships"].append(rel)
                seen_rels.add(rel_key)
    for key in ["policy_pillars", "institutions", "goals", "sectors", "risks"]:
        merged[key] = list(merged[key])
    return merged

def extract_entities_from_file(txt_path, country):
    text = txt_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)[:5]
    all_entities = []
    for i, chunk in enumerate(chunks):
        console.print(f"    chunk {i+1}/{len(chunks)}...", end=" ")
        prompt = EXTRACTION_PROMPT.format(country=country, text=chunk)
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content
            parsed = parse_llm_response(raw)
            if parsed:
                all_entities.append(parsed)
                console.print("[green]✓[/green]")
            else:
                console.print("[yellow]? (parse failed)[/yellow]")
        except Exception as ex:
            console.print(f"[red]✗ ({ex})[/red]")
    return merge_entities(all_entities)

def extract_all_entities():
    txt_files = [f for f in OUT_DIR.glob("*.txt") if "_meta" not in f.name]
    if not txt_files:
        console.print("[red]No extracted text files found. Run extract.py first![/red]")
        return []
    console.print(f"\n[bold blue]Extracting entities from {len(txt_files)} documents using Groq ⚡[/bold blue]\n")
    results = []
    for txt_path in tqdm(txt_files, desc="Extracting entities"):
        country = txt_path.stem.split("_")[0].capitalize()
        console.print(f"\n[bold]{country}[/bold]")
        try:
            entities = extract_entities_from_file(txt_path, country)
            entities["source_file"] = txt_path.name
            out_path = ENTITIES_DIR / f"{txt_path.stem}_entities.json"
            out_path.write_text(json.dumps(entities, indent=2), encoding="utf-8")
            results.append(entities)
            console.print(f"  [green]✓ Saved {len(entities['policy_pillars'])} pillars, "
                          f"{len(entities['institutions'])} institutions, "
                          f"{len(entities['goals'])} goals[/green]")
        except Exception as e:
            console.print(f"  [red]✗ Failed: {e}[/red]")
    console.print(f"\n[bold green]Entity extraction complete! Results in data/entities/[/bold green]\n")
    return results

if __name__ == "__main__":
    extract_all_entities()