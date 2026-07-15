"""
router.py — THE HEART OF THIS PROJECT. This is what makes it more than a
generic "RAG over documents" clone, so this is the file to talk about in your README.

The problem: a plain vector store is great at "find the relevant text" but bad at
"what was the exact number in row X". So after we retrieve the right dataset, we
decide HOW to answer:

  - "descriptive"  -> the answer is prose; let the LLM read the description.
  - "numeric"      -> the answer is a specific figure; go query the actual table.

Below is a deliberately SIMPLE first version so the pipeline runs today.
Your job is to make it smarter — that upgrade IS the interesting part of the project.
"""
from config import settings
from src.llm import generate

# Words that hint the user wants a specific figure (extend these!).
# NOTE: this hand-maintained list is exactly why the keyword router doesn't scale —
# e.g. "what is the population density" has no hint word. The eval catches these gaps;
# the real fix is the LLM intent classifier (see the TODO below).
_NUMERIC_HINTS_EN = ["how many", "number of", "count", "rate", "percentage", "average",
                     "total", "in 20", "density", "how much", "size of"]
_NUMERIC_HINTS_AR = ["كم", "عدد", "نسبة", "متوسط", "إجمالي", "معدل", "كثافة", "حجم"]


def route(question, top_hit):
    """
    Decide the answering path for a question given the best-matching dataset.
    Returns "numeric" or "descriptive".

    Version 1 (works now): combine two weak signals —
      (a) the dataset's own content_type from the catalog, and
      (b) whether the question contains a 'numeric hint' word.
    """
    q = question.lower()
    looks_numeric = (
        any(h in q for h in _NUMERIC_HINTS_EN)
        or any(h in question for h in _NUMERIC_HINTS_AR)
    )
    dataset_is_numeric = top_hit["metadata"].get("content_type") == "numeric"

    if dataset_is_numeric and looks_numeric:
        return "numeric"
    return "descriptive"

    # ------------------------------------------------------------------
    # TODO (the fun upgrade): replace the keyword heuristic above with an
    # LLM classifier. Ask your local model to label the intent. Sketch:
    #
    #   prompt = f'''Classify the question as NUMERIC (needs a specific figure
    #   from a table) or DESCRIPTIVE (needs an explanation). Answer with one word.
    #   Question: {question}'''
    #   label = generate(prompt).lower()
    #   return "numeric" if "numeric" in label else "descriptive"
    #
    # Then in your README, compare the two approaches on your eval set and show
    # which is more accurate. That comparison is exactly the kind of rigor that
    # makes a portfolio project stand out.
    # ------------------------------------------------------------------
