"""Demo 1, second terminal / Slide 06 — RAM footprint of loaded models, live.

Same idea as `ollama ps`, but reads the API so you can show the numbers on a
slide. Prints each currently-loaded model, its size in RAM and CPU/GPU split.

    python experiments/03_ram_usage.py          # once
    python experiments/03_ram_usage.py --watch   # refresh every 2s
"""
from __future__ import annotations

import sys
import time

import requests

from _common import OLLAMA_HOST, check_server


def gb(n: int) -> str:
    return f"{n / 1e9:.1f} GB"


def show() -> None:
    r = requests.get(f"{OLLAMA_HOST}/api/ps", timeout=5)
    r.raise_for_status()
    models = r.json().get("models", [])
    if not models:
        print("No models loaded. Run a demo first (they load on first use).")
        return

    print(f"{'NAME':<22}{'SIZE(RAM)':<12}{'PROCESSOR':<16}{'CONTEXT':<10}")
    print("-" * 60)
    for m in models:
        total = m.get("size", 0)
        vram = m.get("size_vram", 0)
        if total == 0:
            proc = "-"
        elif vram == 0:
            proc = "100% CPU"
        elif vram >= total:
            proc = "100% GPU"
        else:
            proc = f"{100 * vram // total}% GPU"
        ctx = m.get("context_length", "-")
        print(f"{m['name']:<22}{gb(total):<12}{proc:<16}{str(ctx):<10}")


def main() -> None:
    check_server()
    if "--watch" in sys.argv:
        try:
            while True:
                print("\033[2J\033[H", end="")  # clear screen
                print("ollama ps (live, Ctrl-C to stop)\n")
                show()
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nstopped.")
    else:
        show()


if __name__ == "__main__":
    main()
