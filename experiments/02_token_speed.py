"""Demo 1 / Slide 07 — Same prompt, three sizes: watch tokens/sec vs RAM vs quality.

Runs one prompt across the small/mid/large models and prints a comparison table
you can read straight into the "The numbers" slide.

    python experiments/02_token_speed.py
    OLLAMA_SMALL=gemma2:2b OLLAMA_MID=gemma2:9b python experiments/02_token_speed.py
"""
from __future__ import annotations

from _common import (MODEL_LARGE, MODEL_MID, MODEL_SMALL, check_server,
                     ensure_model, generate, tokens_per_second)

PROMPT = ("Ich habe eine Verletzung am Knie. Ich bin 27 Jahre alt. Mein Knie tut weh wenn ich drauf drücke. Das Gelenk fühlt sich aber gut an. Woran könnte es liegen?")

MODELS = [MODEL_SMALL, MODEL_MID, MODEL_LARGE]


def main() -> None:
    check_server()
    print(f"Prompt: {PROMPT}\n")

    rows = []
    for model in MODELS:
        if not ensure_model(model):
            rows.append((model, "—", "not pulled"))
            continue
        print(f"\n{'=' * 60}\n{model}\n{'=' * 60}", flush=True)
        try:
            resp = generate(model, PROMPT, stream=True)  # stream so you see it live
        except Exception as e:  # noqa: BLE001 — keep going if one model fails
            print(f"[!] {model} failed: {e}")
            rows.append((model, "—", "error"))
            continue
        tps = tokens_per_second(resp)
        n = resp.get("eval_count", 0)
        speed = f"{tps:.1f} tok/s" if tps else "n/a"
        print(f"\n# {speed}, {n} tokens")
        rows.append((model, speed, f"{n} tokens"))

    print("\n" + "=" * 52)
    print(f"{'MODEL':<20}{'SPEED':<16}{'OUTPUT':<16}")
    print("-" * 52)
    for model, speed, out in rows:
        print(f"{model:<20}{speed:<16}{out:<16}")
    print("=" * 52)
    print("\nExpect: speed drops and quality rises as the model gets bigger.")


if __name__ == "__main__":
    main()
