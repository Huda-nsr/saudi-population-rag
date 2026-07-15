# 🇸🇦 Saudi Population & Census — Bilingual RAG Q&A

Ask natural-language questions (in **English or Arabic**) about Saudi population and
census data (from the [National Open Data Platform](https://open.data.gov.sa) /
[Saudi Census 2022](https://portal.saudicensus.sa)), and get answers grounded in the
real data — with a citation to the source dataset every time.

> **Demo:** _add a GIF here once it's running (this is the single highest-impact thing in the README)._
> **Live app:** _add your Hugging Face Spaces link here._

---

## Why this project is interesting (read this part)

Most "RAG" projects embed a pile of PDFs and call it done. Open government data is
different: it's mostly **tables of numbers** (population by region, age, nationality),
and it's **bilingual**. Both facts break the naive approach, and handling them is the
point of this project.

**Design decision — route, don't just retrieve.** A vector store is good at
*finding the right dataset* but bad at *reading an exact figure out of a table*.
So the pipeline has two paths:

1. **Semantic search over metadata** — embed dataset titles, descriptions, and
   column names (in both languages) to find the *right dataset* for a question.
2. **A router** then decides: is this a *descriptive* question (answer from text)
   or a *numeric* one (go query the actual CSV)? Numeric questions are answered
   from the real rows, not a fuzzy text match.

That "retrieve with embeddings, answer with a structured lookup" split is the
thing to talk about in an interview. See `src/router.py` and `src/table_query.py`.

**Bilingual by construction.** A single multilingual embedding model
(`intfloat/multilingual-e5-large`) plus storing English + Arabic text in the same
document means a question in *either* language matches the same dataset.

---

## Architecture

```
question (EN or AR)
      │
      ▼
  embed_store.search()      ← multilingual embeddings + Chroma  (find the dataset)
      │
      ▼
  router.route()            ← numeric vs descriptive?           (the key decision)
      │
      ├── numeric ──▶ table_query.answer_from_table()  ← reads the real CSV
      │
      └── descriptive ─▶ rag._answer_descriptive()     ← explains from the text
      │
      ▼
  answer + SOURCE citation  ← every answer says where it came from
```

Everything runs **locally** via [Ollama](https://ollama.com) — no API keys, no data
leaves your machine.

---

## Setup

```bash
# 1. Install Python deps
pip install -r requirements.txt

# 2. Install Ollama (https://ollama.com/download) and pull a bilingual model
ollama pull qwen2.5:7b

# 3. Get data
#    Quickstart (runs immediately with synthetic sample data):
python make_sample_data.py
#    Real data: curate datasets in data/catalog.json and drop their CSVs in
#    data/raw/ — see CURATION.md. (The portal is WAF-protected, so CSVs are
#    downloaded once via the browser and cached locally.)

# 4. Build the vector index from the catalog
python scripts/build_index.py

# 5. Run the app
python app.py
```

Evaluate the system (routing accuracy by language and path):

```bash
python -m eval.run_eval --routing   # fast: retrieval + routing only, no LLM
python -m eval.run_eval             # full: also scores the LLM answers
```

You can also query from the command line:

```bash
python -m src.rag "What was the population of the Riyadh region in 2022?"
python -m src.rag "كم عدد سكان منطقة مكة المكرمة؟"
```

---

## Project layout

| Path | What it does |
|---|---|
| `data/catalog.json` | **You curate this.** The index of datasets you support. |
| `src/ingest.py` | Turns catalog entries into searchable text (both languages). |
| `src/embed_store.py` | Multilingual embeddings + Chroma vector store. |
| `src/router.py` | **The core idea** — numeric vs descriptive routing. |
| `src/table_query.py` | Answers numeric questions from the real CSV. |
| `src/rag.py` | Orchestrates the whole flow into `answer()`. |
| `src/llm.py` | Local Ollama client. |
| `app.py` | Gradio demo UI (bilingual example buttons). |
| `eval/eval_questions.json` | **Your test set** — score answers pass/fail. |

---

## Evaluation

`eval/eval_questions.json` holds hand-written Q&A pairs. Run them through `answer()`
and report accuracy, broken down by language and by answering path. Most portfolio
RAG projects skip evaluation entirely — having one sets yours apart.

---

## What worked / what didn't

A concrete example from building this — **the eval caught a retrieval bug.**
An early catalog carried a "synthetic sample data" disclaimer inside every dataset's
`description`. Because `ingest.py` embeds the description, that shared boilerplate
pulled the numeric datasets together in vector space and blurred what distinguished
them. An easy eval hid it; adversarial paraphrases (a question without the one word
that disambiguates which table it needs) exposed it, dropping routing accuracy and
sending queries to the wrong dataset. The fix: keep the embedded description *about
the data* — move disclaimers to a `sample_data` flag surfaced in the UI, and put the
terms users actually type (region *values* like "Riyadh", not just the column name
"region") into the description. Rebuilding the index restored routing to 100%.
Lesson: *an eval only helps if its cases are hard enough to fail — and what you embed
is as important as which model you embed with.*

Scaling from 4 to 6 datasets sharpened the point: with several "X by administrative
region" tables (population, nationality, households, density), short Arabic queries
became hard for the bi-encoder to separate — tuning a description to fix one case
(density) regressed another (plain population), a clear whack-a-mole signal. Routing
holds at ~13/14; the honest fix is not more description-tuning but a **cross-encoder
reranker** (or LLM-based dataset selection) on the top-k retrieved candidates. That's
the next item on the roadmap, and the eval is what makes the trade-off visible.

---

## Roadmap / future work

- Replace the keyword router with an LLM intent classifier and compare on the eval set.
- Text-to-pandas for large tables (with a sandboxed execution namespace).
- Support more themes beyond education (health, economy).
- Add a hosted-API backend option alongside Ollama.

---

## Data & license

Datasets are from the Saudi National Open Data Platform under the Open Data Commons
Attribution License — attribution to the source entity is required and preserved in
each answer's citation. This project is for educational/portfolio use.
