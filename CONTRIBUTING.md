# Contributing to the African AI Policy Knowledge Graph

Thank you for your interest in this project. Every contribution,  big or small, helps build a better picture of AI governance across Africa.

---

## The Easiest Way to Contribute: Add a Policy Document

The most impactful thing you can do is find and submit an official AI policy PDF from an African country we don't have yet.

### Which countries are we missing?

We currently have policies loaded for: Kenya, Rwanda, Ghana, Zambia, Egypt, Nigeria, Senegal, and the African Union.

Countries we still need (among others):
- Morocco, Tunisia, Algeria
- South Africa, Ethiopia, Uganda
- Mauritius, Tanzania, Côte d'Ivoire
- And many more

### How to find the right document

Look for official government sources, ministry of technology, ministry of digital affairs, or the national AI council. The document should be:
- An official national AI strategy or policy
- Downloadable as a PDF
- In English or French (both work)

### How to name the file

Use this format:
```
countryname_ai_strategy_year.pdf
```

Examples:
```
morocco_ai_strategy_2023.pdf
ethiopia_ai_strategy_2024.pdf
southafrica_ai_strategy_2022.pdf
```

The first word of the filename is used as the country name in the graph, so keep it clean and lowercase.

### How to submit

1. Fork this repository
2. Add your PDF to `data/policies/`
3. Open a Pull Request with:
   - The country name
   - The source URL where you found the document
   - The year of the document

That's it. We handle the rest,  running the pipeline, updating the graph, and deploying.

---

## Other Ways to Contribute

**Fix a bug**  open an issue or submit a PR directly.

**Improve entity extraction**  the prompts in `src/entity_extractor.py` can always be better. If you notice the LLM missing important pillars or goals from a document, suggest an improved prompt.

**Improve the frontend**  the UI in `frontend/index.html` is intentionally simple. If you have design or frontend skills, improvements are welcome.

**Add a new country to the "no policy" list**  if you know an African country that should be in the graph but isn't listed in `src/graph_loader.py`, open a PR to add it.

---

## Ground Rules

- Be respectful and constructive
- Only submit official government documents, not summaries or third-party analyses
- If a country has both English and French versions, prefer English but French is also accepted
- Don't submit documents that require a login or paywall to access

---

## Questions?

Open an issue and we'll get back to you. This project is built in the open and we welcome anyone who cares about AI governance in Africa.
