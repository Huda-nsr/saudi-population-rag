"""
run_eval.py — measure the system against hand-written cases in eval_questions.json.

It scores two things SEPARATELY (separating them is what makes it useful for
debugging), and breaks each down BY LANGUAGE (ar/en) and BY ANSWERING PATH
(numeric/descriptive):

  - ROUTING   : did we retrieve the right dataset AND pick the right path?
                (needs the vector index; no LLM call, so it's fast + deterministic)
  - ANSWER    : does the final answer contain the expected substring?
                (calls Ollama via answer(), so it's slower)

Run:  python -m eval.run_eval            # routing + answers
      python -m eval.run_eval --routing  # routing only (skip the slow LLM answers)

Prereqs: build the index first  ->  python scripts/build_index.py
"""

import argparse
import json
import pathlib
from collections import defaultdict

from src.embed_store import search
from src.rerank import select_dataset
from src.router import route
from src.rag import answer

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL_PATH = ROOT / "eval" / "eval_questions.json"


def _pct(n, d):
    return f"{n}/{d} ({(n / d if d else 0):.0%})"


def run(routing_only: bool) -> None:
    with open(EVAL_PATH, encoding="utf-8") as f:
        cases = json.load(f)["questions"]

    # tallies: overall + per-language + per-expected-path
    routing_ok = answer_ok = answer_scored = 0
    by_lang = defaultdict(lambda: {"route": 0, "n": 0})
    by_path = defaultdict(lambda: {"route": 0, "n": 0})

    for c in cases:
        q = c["question"]
        lang = c.get("language", "?")
        exp_ds = c.get("expected_dataset")
        exp_path = c.get("expected_type")  # "numeric" | "descriptive"

        hits = search(q)
        top = select_dataset(q, hits) if hits else None  # LLM reranks the top-k
        chosen_id = top["metadata"].get("id") if top else None
        got_path = route(q, top) if top else None

        ds_ok = chosen_id == exp_ds
        path_ok = got_path == exp_path
        route_hit = ds_ok and path_ok
        routing_ok += route_hit
        by_lang[lang]["n"] += 1
        by_lang[lang]["route"] += route_hit
        by_path[exp_path]["n"] += 1
        by_path[exp_path]["route"] += route_hit

        flag = "PASS" if route_hit else "FAIL"
        print(f"[{flag}] ({lang}/{exp_path}) {q[:55]}")
        if not ds_ok:
            print(f"         dataset: expected {exp_ds}, got {chosen_id}")
        if not path_ok:
            print(f"         path:    expected {exp_path}, got {got_path}")

        if not routing_only:
            expect = c.get("expected_answer_contains", "")
            result = answer(q)
            text = (result.get("answer") or "").lower()
            if expect and not expect.startswith("REPLACE"):
                answer_scored += 1
                if expect.lower() in text:
                    answer_ok += 1
                else:
                    print(f"         answer missing expected substring: {expect!r}")

    total = len(cases)
    print("\n================ SCORECARD ================")
    print(f"ROUTING accuracy (dataset + path): {_pct(routing_ok, total)}")
    print("  by language:")
    for lang, t in sorted(by_lang.items()):
        print(f"    {lang:3} : {_pct(t['route'], t['n'])}")
    print("  by expected path:")
    for path, t in sorted(by_path.items()):
        print(f"    {path:11} : {_pct(t['route'], t['n'])}")
    if not routing_only:
        print(f"\nANSWER accuracy (substring match): {_pct(answer_ok, answer_scored)}"
              f"  [{total - answer_scored} case(s) had no expected substring set]")
    print("===========================================")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--routing", action="store_true",
                    help="skip the slow LLM answer step; score routing only")
    args = ap.parse_args()
    run(routing_only=args.routing)
