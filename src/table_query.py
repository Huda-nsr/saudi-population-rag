"""
table_query.py — the "numeric" answering path.

When the router decides a question needs a real figure (not prose), we load the
dataset's actual CSV and pull the number, instead of hoping the LLM guessed right.

Version 1 (works now): load the CSV and hand a small preview to the LLM, asking it
to read the number off the table. This already beats pure vector search because the
LLM is looking at the REAL rows, not a fuzzy text match.

The upgrade path (TODO below) is text-to-SQL / real filtering, which is more robust.
"""
import pandas as pd
from config import settings
from src.llm import generate


def _load_table(file_name):
    """Load a dataset CSV from data/raw. Returns a DataFrame or None."""
    path = settings.RAW_DATA_DIR / file_name
    if not path.exists():
        return None
    # Saudi open data is often UTF-8 with Arabic headers; utf-8-sig handles BOMs.
    return pd.read_csv(path, encoding="utf-8-sig")


def answer_from_table(question, top_hit):
    """Answer a numeric question by looking at the real table."""
    file_name = top_hit["metadata"].get("file", "")
    df = _load_table(file_name)

    if df is None:
        return (f"I found the right dataset ({top_hit['metadata'].get('title_en')}), "
                f"but its data file '{file_name}' isn't downloaded into data/raw yet.")

    # Give the model a compact, honest view of the table to read from.
    # For small tables this is enough; for big ones you'll want the TODO below.
    preview = df.head(50).to_csv(index=False)

    prompt = (
        "You are reading a table from Saudi open education data. "
        "Answer the user's question using ONLY the rows below. "
        "If the answer isn't present, say so plainly. "
        "Reply in the same language as the question.\n\n"
        f"Question: {question}\n\n"
        f"Table (CSV):\n{preview}"
    )
    return generate(prompt)

    # ------------------------------------------------------------------
    # TODO (robustness upgrade): for tables too big to fit in the prompt,
    # generate a pandas/SQL query instead of pasting rows. Sketch:
    #
    #   1. Show the LLM only the column names + 3 sample rows.
    #   2. Ask it to write a single pandas expression that computes the answer,
    #      e.g.  df[df.region == "Riyadh"].school_count.sum()
    #   3. eval() it in a SANDBOXED, restricted namespace (never raw eval on
    #      untrusted output — allow only df + a whitelist).
    #   4. Feed the computed value back to the LLM to phrase the final sentence.
    #
    # This "text-to-pandas" pattern scales to large datasets and is a great thing
    # to write up. Mention the safety consideration (sandboxing) — reviewers notice.
    # ------------------------------------------------------------------
