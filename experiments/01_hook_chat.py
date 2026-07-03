"""Demo 0 — The hook: a capable LLM answering, fully local.

Slide: "This just ran on this laptop." Run BEFORE any slides. WiFi can be off.

    python experiments/01_hook_chat.py
    python experiments/01_hook_chat.py "Warum gibt es Bielefeld wirklich?"
"""
from __future__ import annotations

import sys

from _common import MODEL_SMALL, check_server, ensure_model, generate, tokens_per_second

DEFAULT_PROMPT = "Erkläre in 3 Sätzen, warum Bielefeld existiert."


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or DEFAULT_PROMPT
    check_server()
    ensure_model(MODEL_SMALL)

    print(f"\n$ ollama run {MODEL_SMALL}")
    print(f">>> {prompt}\n")

    resp = generate(MODEL_SMALL, prompt, stream=True)

    tps = tokens_per_second(resp)
    if tps:
        print(f"\n# {MODEL_SMALL} · CPU only · ~{tps:.0f} tokens/s — no network needed")


if __name__ == "__main__":
    main()
