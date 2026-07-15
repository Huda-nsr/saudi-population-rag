"""
llm.py — talk to your LOCAL model running in Ollama.

Prereqs (one-time):
  1. Install Ollama:  https://ollama.com/download
  2. Pull a bilingual model:  ollama pull qwen2.5:7b
  3. Ollama runs a server on http://localhost:11434 automatically.

Everything here is just HTTP — no API keys, nothing leaves your machine.
"""
import requests
from config import settings


def generate(prompt, system=None, temperature=0.2):
    """
    Send a prompt to Ollama and return the model's text answer.
    Low temperature (0.2) keeps answers factual — good for a data Q&A tool.
    """
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,                 # get the whole answer at once (simpler)
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system

    try:
        r = requests.post(f"{settings.OLLAMA_URL}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["response"].strip()
    except requests.exceptions.ConnectionError:
        return ("[Ollama not reachable. Is it running? Try `ollama serve` and "
                "`ollama pull qwen2.5:7b`.]")
    except requests.exceptions.RequestException as e:
        return f"[LLM error: {e}]"


if __name__ == "__main__":
    # Quick check that your local model responds: python -m src.llm
    print(generate("Say hello in English and Arabic in one short line."))
