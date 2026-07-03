"""Download + build the fine-tuning dataset for the LoRA demo.

Produces `experiments/lora/data/train.jsonl` in chat format:
    {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}

Two sources are combined:
  1. A real German instruction dataset pulled from the Hugging Face Hub
     (default: FreedomIntelligence/alpaca-gpt4-deutsch) — gives natural German
     instruction/response pairs.
  2. A small hand-written "Amtsdeutsch" style set so the LoRA has a clear,
     demo-able personality (plain question -> reply in formal officialese).

    python experiments/lora/prepare_dataset.py
    python experiments/lora/prepare_dataset.py --hf-only --limit 1000
    python experiments/lora/prepare_dataset.py --style-only
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")
OUT = os.path.join(DATA_DIR, "train.jsonl")

HF_DATASET = "FreedomIntelligence/alpaca-gpt4-deutsch"

# A compact style seed: everyday question -> stiff Amtsdeutsch answer.
# Enough to teach a recognisable tone for the live demo.
STYLE_SEED = [
    ("Kann ich meinen Hund anmelden?",
     "Die Anmeldung eines Hundes ist gemäß der geltenden Hundesteuersatzung "
     "innerhalb eines Monats nach Aufnahme des Tieres bei der zuständigen "
     "Stelle schriftlich vorzunehmen."),
    ("Wo parke ich am besten?",
     "Es wird darauf hingewiesen, dass die Nutzung der ausgewiesenen "
     "öffentlichen Stellflächen unter Beachtung der jeweils geltenden "
     "Parkraumbewirtschaftung zu erfolgen hat."),
    ("Wann hat das Amt auf?",
     "Die Öffnungszeiten der Dienststelle sind den amtlichen Bekanntmachungen "
     "zu entnehmen; eine vorherige Terminvereinbarung wird ausdrücklich empfohlen."),
    ("Ich will umziehen, was muss ich tun?",
     "Im Falle eines Wohnsitzwechsels ist die betroffene Person verpflichtet, "
     "sich innerhalb der gesetzlich vorgesehenen Frist bei der Meldebehörde "
     "an- bzw. umzumelden."),
    ("Wie viel kostet ein neuer Ausweis?",
     "Die Gebühr für die Ausstellung eines Personalausweises richtet sich nach "
     "der einschlägigen Gebührenordnung und ist bei Antragstellung zu entrichten."),
    ("Kann ich meinen Müll hier hinstellen?",
     "Die Ablagerung von Abfällen ist ausschließlich im Rahmen der satzungs"
     "gemäßen Abfallentsorgung und zu den bekannt gegebenen Zeiten zulässig."),
    ("Darf ich hier grillen?",
     "Das Grillen in öffentlichen Grünanlagen ist nur auf den hierfür "
     "ausdrücklich freigegebenen Flächen und unter Beachtung der geltenden "
     "Brandschutzbestimmungen gestattet."),
    ("Wie melde ich ein Schlagloch?",
     "Schäden an der öffentlichen Verkehrsfläche können unter Angabe des "
     "genauen Standorts bei der zuständigen Stelle zur weiteren Veranlassung "
     "gemeldet werden."),
]

SYSTEM = ("Du bist ein Assistent der Stadtverwaltung und antwortest stets in "
          "korrektem, förmlichem Amtsdeutsch.")


def style_examples() -> list[dict]:
    rows = []
    for q, a in STYLE_SEED:
        rows.append({"messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": q},
            {"role": "assistant", "content": a},
        ]})
    return rows


def hf_examples(limit: int) -> list[dict]:
    from datasets import load_dataset

    print(f"[.] Downloading '{HF_DATASET}' from the Hugging Face Hub …")
    ds = load_dataset(HF_DATASET, split="train")
    print(f"[.] Loaded {len(ds):,} rows; keeping first {limit}.")

    cols = ds.column_names
    _ROLE = {"human": "user", "user": "user", "gpt": "assistant",
             "assistant": "assistant", "system": "system"}
    rows = []
    for ex in ds.select(range(min(limit, len(ds)))):
        if "conversations" in cols:  # ShareGPT format: [{"from","value"}, ...]
            msgs = [{"role": _ROLE.get(t["from"], "user"),
                     "content": (t["value"] or "").strip()}
                    for t in ex["conversations"] if t.get("value")]
        else:  # instruction/input/output format
            instr_key = next((k for k in ("instruction", "prompt", "question") if k in cols), None)
            out_key = next((k for k in ("output", "response", "answer", "completion") if k in cols), None)
            if not instr_key or not out_key:
                raise SystemExit(f"[!] Unexpected columns {cols}; adjust prepare_dataset.py")
            user = ex[instr_key]
            if ex.get("input"):
                user = f"{user}\n\n{ex['input']}"
            msgs = [{"role": "user", "content": (user or "").strip()},
                    {"role": "assistant", "content": (ex[out_key] or "").strip()}]
        if len(msgs) >= 2 and all(m["content"] for m in msgs):
            rows.append({"messages": msgs})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500,
                    help="max rows to keep from the HF dataset")
    ap.add_argument("--hf-only", action="store_true")
    ap.add_argument("--style-only", action="store_true")
    args = ap.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    rows: list[dict] = []

    if not args.hf_only:
        rows += style_examples()
    if not args.style_only:
        try:
            rows += hf_examples(args.limit)
        except Exception as e:  # noqa: BLE001 — keep the demo resilient offline
            print(f"[!] HF download failed ({e}). Writing style-only dataset.")

    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[✓] Wrote {len(rows):,} examples -> {OUT}")


if __name__ == "__main__":
    main()
