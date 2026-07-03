"""Shared helpers for the Ollama live-demo scripts.

All demos talk to a locally running Ollama server (`ollama serve`, default
http://localhost:11434). Model names default to the ones on the slides but can
be overridden with environment variables so you can adapt to whatever you have
actually pulled, e.g.:

    OLLAMA_SMALL=gemma2:2b OLLAMA_MID=gemma2:9b python experiments/02_token_speed.py
"""
from __future__ import annotations

import os
import sys
import time

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Model names as used on the slides (mid-2026). Override via env if your local
# Ollama library uses different tags.
MODEL_SMALL = os.environ.get("OLLAMA_SMALL", "gemma4:e2b")
MODEL_MID = os.environ.get("OLLAMA_MID", "gemma4:e4b")
MODEL_LARGE = os.environ.get("OLLAMA_LARGE", "gemma4:12b")
MODEL_VISION = os.environ.get("OLLAMA_VISION", MODEL_MID)
MODEL_CODER = os.environ.get("OLLAMA_CODER", "qwen3.6:27b")


def check_server() -> None:
    """Exit with a friendly message if Ollama isn't reachable."""
    try:
        requests.get(f"{OLLAMA_HOST}/api/version", timeout=3)
    except requests.exceptions.RequestException:
        sys.exit(
            f"[!] Cannot reach Ollama at {OLLAMA_HOST}.\n"
            f"    Start it with:  ollama serve\n"
            f"    (or set OLLAMA_HOST to point somewhere else)"
        )


def list_models() -> list[str]:
    r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
    r.raise_for_status()
    return [m["name"] for m in r.json().get("models", [])]


def ensure_model(model: str) -> bool:
    """Return True if `model` is available locally, else print a hint.

    Matching is exact on the full `name:tag`. Only when the caller gives a bare
    name (no tag) do we fall back to matching any tag of that base — otherwise a
    pulled `gemma4:e2b` would wrongly satisfy a request for `gemma4:12b`.
    """
    names = list_models()
    if model in names:
        return True
    if ":" not in model and any(n.split(":")[0] == model for n in names):
        return True
    print(f"[!] Model '{model}' not found locally. Pull it with:  ollama pull {model}")
    return False


def generate(model: str, prompt: str, images: list[str] | None = None,
             stream: bool = False, options: dict | None = None) -> dict:
    """Call /api/generate. With stream=False returns the full response dict
    (including timing fields eval_count / eval_duration used for tokens/s)."""
    payload: dict = {"model": model, "prompt": prompt, "stream": stream}
    if images:
        payload["images"] = images
    if options:
        payload["options"] = options

    if not stream:
        r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=600)
        r.raise_for_status()
        return r.json()

    # Streaming: print tokens as they arrive, accumulate final stats.
    final: dict = {}
    with requests.post(f"{OLLAMA_HOST}/api/generate", json=payload,
                       stream=True, timeout=600) as r:
        r.raise_for_status()
        import json as _json
        for line in r.iter_lines():
            if not line:
                continue
            chunk = _json.loads(line)
            if chunk.get("response"):
                print(chunk["response"], end="", flush=True)
            if chunk.get("done"):
                final = chunk
        print()
    return final


def tokens_per_second(resp: dict) -> float | None:
    """Compute generation speed from an Ollama response dict."""
    ec = resp.get("eval_count")
    ed = resp.get("eval_duration")  # nanoseconds
    if ec and ed:
        return ec / (ed / 1e9)
    return None


def timed(label: str):
    """Tiny context-manager for wall-clock timing in demos."""
    class _T:
        def __enter__(self):
            self.t0 = time.time()
            return self

        def __exit__(self, *exc):
            print(f"  ({label}: {time.time() - self.t0:.1f}s wall clock)")

    return _T()
