"""
extract.py
----------
Reads all PDFs from data/policies/ and extracts clean text.
Saves each as a .txt file in data/extracted/
"""

import os
import json
import pdfplumber
from pathlib import Path
from tqdm import tqdm
from rich.console import Console

console = Console()

PDF_DIR  = Path("data/policies")
OUT_DIR  = Path("data/extracted")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Basic cleaning: remove excessive whitespace."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if l]           # drop empty lines
    return "\n".join(lines)


def extract_pdf(pdf_path: Path) -> dict:
    """Extract text from a single PDF. Returns dict with metadata."""
    country = pdf_path.stem.split("_")[0].capitalize()
    pages_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(clean_text(text))

    full_text = "\n\n".join(pages_text)
    return {
        "country": country,
        "filename": pdf_path.name,
        "num_pages": len(pages_text),
        "text": full_text,
    }


def extract_all():
    """Extract text from all PDFs in PDF_DIR."""
    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        console.print(f"[red]No PDFs found in {PDF_DIR}[/red]")
        console.print("Make sure you downloaded the PDFs first!")
        return []

    console.print(f"\n[bold blue]Found {len(pdf_files)} PDFs[/bold blue]\n")
    results = []

    for pdf_path in tqdm(pdf_files, desc="Extracting PDFs"):
        try:
            data = extract_pdf(pdf_path)
            # Save text file
            out_path = OUT_DIR / f"{pdf_path.stem}.txt"
            out_path.write_text(data["text"], encoding="utf-8")
            # Save metadata
            meta_path = OUT_DIR / f"{pdf_path.stem}_meta.json"
            meta_path.write_text(
                json.dumps({k: v for k, v in data.items() if k != "text"}, indent=2),
                encoding="utf-8"
            )
            results.append(data)
            console.print(f"  [green]✓[/green] {data['country']} — {data['num_pages']} pages extracted")
        except Exception as e:
            console.print(f"  [red]✗ Failed: {pdf_path.name} → {e}[/red]")

    console.print(f"\n[bold green]Extraction complete! {len(results)} files saved to {OUT_DIR}[/bold green]\n")
    return results


if __name__ == "__main__":
    extract_all()