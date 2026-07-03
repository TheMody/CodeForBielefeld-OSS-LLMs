"""Demo / Slide 10 — Quantization: "JPEG for neural networks".

Runs the SAME prompt through a q4 and a q8 build of the same model and prints
size, speed and output side by side. The point of the slide: you will barely
spot the quality difference, but q8 uses ~2x the RAM.

    # first pull both quant builds, e.g.:
    #   ollama pull gemma4:e2b            # default q4_K_M
    #   ollama pull gemma4:e2b-it-q8_0
    OLLAMA_Q4=gemma4:e2b OLLAMA_Q8=gemma4:e2b-it-q8_0 \
        python experiments/05_quantization_compare.py
"""
from __future__ import annotations

import os

import requests

from _common import (OLLAMA_HOST, check_server, ensure_model, generate,
                     tokens_per_second)

MODEL_Q4 = os.environ.get("OLLAMA_Q4", "gemma4:e2b")
MODEL_Q8 = os.environ.get("OLLAMA_Q8", "gemma4:e2b-it-q8_0")

PROMPT = "Erkläre in zwei Sätzen, was Quantisierung bei neuronalen Netzen bedeutet."


def loaded_ram(model: str) -> str:
    r = requests.get(f"{OLLAMA_HOST}/api/ps", timeout=5).json()
    for m in r.get("models", []):
        if m["name"].split(":")[0] == model.split(":")[0] and model.split(":")[-1] in m["name"]:
            return f"{m.get('size', 0) / 1e9:.1f} GB"
    return "?"


def run(model: str) -> None:
    if not ensure_model(model):
        return
    print(f"\n{'=' * 60}\n{model}\n{'=' * 60}")
    resp = generate(model, PROMPT, stream=True)
    tps = tokens_per_second(resp)
    print(f"# RAM loaded: {loaded_ram(model)}   speed: "
          f"{tps:.1f} tok/s" if tps else "# (no timing)")


def main() -> None:
    check_server()
    print(f"Prompt: {PROMPT}")
    for model in (MODEL_Q4, MODEL_Q8):
        run(model)
    print("\nSpoiler: the answers are near-identical; q8 just costs more RAM.")


if __name__ == "__main__":
    main()
