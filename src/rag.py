"""
rag.py — the conductor. This ties every piece together into one function: answer().

Flow:
  question
    -> search()   find the most relevant dataset(s)          [embed_store.py]
    -> route()    decide: numeric lookup vs descriptive        [router.py]
    -> answer     either query the table or explain from text  [table_query.py / here]
    -> attach the SOURCE so every answer is grounded + citable

Grounding + citation is the whole point of RAG. We always return where the answer
came from, so the user (and you, when debugging) can verify it.
"""
from src.embed_store import search
from src.router import route
from src.table_query import answer_from_table
from src.llm import generate


def _answer_descriptive(question, top_hit):
    """Prose answer: let the LLM explain using the dataset's description text."""
    prompt = (
        "You are a helpful assistant for Saudi open education data. "
        "Use the dataset information below to answer. If it doesn't contain the "
        "answer, say so. Reply in the same language as the question.\n\n"
        f"Question: {question}\n\n"
        f"Dataset info:\n{top_hit['document']}"
    )
    return generate(prompt)


def answer(question):
    """Answer a user question end to end. Returns a dict: text + source."""
    hits = search(question)
    if not hits:
        return {"answer": "I couldn't find a relevant dataset for that.", "source": None}

    top_hit = hits[0]
    path = route(question, top_hit)  # "numeric" or "descriptive"

    if path == "numeric":
        text = answer_from_table(question, top_hit)
    else:
        text = _answer_descriptive(question, top_hit)

    # Always hand back the source for citation/grounding.
    source = {
        "dataset": top_hit["metadata"].get("title_en"),
        "url": top_hit["metadata"].get("source_url"),
        "path_used": path,
        # True when the demo answered a numeric question off synthetic sample data,
        # so the UI can flag it honestly (the cited URL is real; the figures aren't).
        "sample_data": bool(top_hit["metadata"].get("sample_data", False)) and path == "numeric",
    }
    return {"answer": text, "source": source}


if __name__ == "__main__":
    # Try it from the command line: python -m src.rag
    import sys
    q = " ".join(sys.argv[1:]) or "How many schools are there per region?"
    result = answer(q)
    print("\nANSWER:\n", result["answer"])
    print("\nSOURCE:\n", result["source"])
