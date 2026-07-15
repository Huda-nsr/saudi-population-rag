"""
rerank.py — LLM-based dataset selection over the top-k retrieved candidates.

Why: bi-encoder retrieval (embed_store.search) reliably surfaces the RIGHT FEW
datasets, but on short queries it can mis-RANK near-identical ones — e.g. it put
"Population density by region" above "Population by administrative region" for
"كم عدد سكان منطقة مكة المكرمة؟" (a plain population question). No amount of
description-tuning fixes that cleanly without regressing another case.

So instead of blindly trusting the vector top-1, we hand the top-k candidates to
the local LLM and let it pick the best one for THIS question. The model reasons
over the titles in both languages, which separates 'population' from 'density'
easily. On any hiccup (LLM unreachable, unparseable reply, out-of-range index) we
fall back to the vector top-1 — so reranking never does worse than pure retrieval.
"""
import re

from src.llm import generate


def select_dataset(question, hits):
    """Return the best-matching hit for the question from the retrieved candidates."""
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]

    # Bilingual menu with a description snippet per candidate. Titles alone aren't
    # enough (e.g. "Saudis in Riyadh" needs the *nationality* dataset, not the region
    # one) — the description/columns tell the model what each table actually contains.
    def _snippet(h):
        doc = (h.get("document") or "").replace("passage: ", "")
        return " ".join(doc.split())[:240]

    menu = "\n".join(
        f"{i}. {h['metadata'].get('title_en','')} / {h['metadata'].get('title_ar','')}\n"
        f"   {_snippet(h)}"
        for i, h in enumerate(hits, 1)
    )
    prompt = (
        "Pick the ONE dataset that best answers the question. Match the specific "
        "breakdown the question asks for (e.g. nationality vs region vs age vs density). "
        "Consider both English and Arabic. Reply with ONLY the number.\n\n"
        f"Question: {question}\n\n"
        f"Datasets:\n{menu}\n\n"
        "Best dataset number:"
    )

    reply = generate(prompt, temperature=0.0)
    match = re.search(r"\d+", reply or "")
    if not match:
        return hits[0]                      # unparseable -> trust retrieval
    idx = int(match.group()) - 1
    return hits[idx] if 0 <= idx < len(hits) else hits[0]
