"""Demo / Slide 13 — Pick the model for the task: Gemma vs Qwen on real code.

Gives both models the same non-trivial coding task. On this laptop the small
Gemma often struggles while the Qwen coder nails it (run the Qwen row on bigger
hardware or point OLLAMA_HOST at a rented GPU box).

    python experiments/06_coding_compare.py
    OLLAMA_HOST=http://gpu-box:11434 python experiments/06_coding_compare.py
"""
from __future__ import annotations

from _common import (MODEL_CODER, MODEL_MID, check_server, ensure_model,
                     generate, tokens_per_second)

TASK = (
    "Write a Python function `merge_intervals(intervals)` that takes a list of "
    "[start, end] pairs, merges all overlapping intervals, and returns the "
    "sorted result. Include a docstring and 3 assert-based tests."
)

MODELS = [MODEL_MID, MODEL_CODER]


def main() -> None:
    check_server()
    print(f"TASK:\n{TASK}\n")
    for model in MODELS:
        if not ensure_model(model):
            continue
        print(f"\n{'#' * 64}\n# {model}\n{'#' * 64}")
        resp = generate(model, TASK, stream=True)
        tps = tokens_per_second(resp)
        if tps:
            print(f"\n# {model}: {tps:.1f} tok/s")
    print("\nCompare: does the code run? are the tests correct? which reads cleaner?")


if __name__ == "__main__":
    main()
