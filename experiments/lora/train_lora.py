"""Slide 12 — Fine-tuning at home with LoRA / QLoRA.

Trains a small LoRA adapter on the dataset from `prepare_dataset.py`. Uses the
portable Hugging Face stack (transformers + peft + trl) so it runs on this
CPU-only laptop for a smoke test, and on a GPU (or free Colab T4) for the real
run. On a GPU with `bitsandbytes` installed (`uv sync --extra gpu`) it switches
to 4-bit QLoRA automatically.

    # smoke test (2 steps) to prove the pipeline — fast on GPU, slow on CPU:
    python experiments/lora/train_lora.py --smoke

    # real run (point at a GPU box):
    python experiments/lora/train_lora.py

The default base is Gemma 4 E4B-it — the exact model from the slides. It is a
*gated* model on the Hugging Face Hub: accept the license on its model page and
authenticate once (`uv run huggingface-cli login`, or set HF_TOKEN) before the
first download (~8 GB). Override with e.g. BASE_MODEL=google/gemma-4-E2B-it for
a smaller/faster run.

For the talk itself the slides suggest the Unsloth Colab notebook with the same
Gemma 4 base — this script is the "here's what actually happens" companion.
"""
from __future__ import annotations

import argparse
import os

import torch

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data", "train.jsonl")
OUT_DIR = os.path.join(HERE, "adapter")

# Gemma 4 E4B instruction-tuned — the model from the slides. Gated on the HF
# Hub (accept the license + `huggingface-cli login`). Use google/gemma-4-E2B-it
# for a lighter run. Note: a full run wants a GPU; on CPU it is only a smoke test.
BASE_MODEL = os.environ.get("BASE_MODEL", "google/gemma-4-E2B-it")


def _warn_cpu_ram() -> None:
    """Warn early if there likely isn't enough RAM to load the base on CPU.

    Loading is memory-bound: bf16 weights (~2 bytes/param) plus overhead. On a
    RAM-tight box, prefer the GPU/Colab path or the smaller google/gemma-4-E2B-it.
    """
    try:
        import psutil  # optional
        avail = psutil.virtual_memory().available / 1e9
    except Exception:  # noqa: BLE001 — psutil not installed; read /proc directly
        avail = None
        try:
            with open("/proc/meminfo") as fh:
                for line in fh:
                    if line.startswith("MemAvailable:"):
                        avail = int(line.split()[1]) / 1e6  # kB -> GB
                        break
        except OSError:
            return
    if avail is not None and avail < 20:
        print(f"[!] Only ~{avail:.0f} GB RAM free. Gemma 4 E4B needs ~16 GB just "
              f"to load (bf16) plus training overhead — this may get OOM-killed.\n"
              f"    Safer options: run on a GPU/Colab, or "
              f"BASE_MODEL=google/gemma-4-E2B-it for a smaller base.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="2 steps only, to prove the pipeline works")
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--rank", type=int, default=16)
    args = ap.parse_args()

    if not os.path.exists(DATA):
        raise SystemExit("[!] No dataset. Run: python experiments/lora/prepare_dataset.py")

    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    use_cuda = torch.cuda.is_available()
    print(f"[.] Device: {'CUDA' if use_cuda else 'CPU'} | base: {BASE_MODEL}")

    # QLoRA (4-bit) only on GPU with bitsandbytes; otherwise plain LoRA.
    quant_cfg = None
    if use_cuda:
        try:
            from transformers import BitsAndBytesConfig
            quant_cfg = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            print("[.] Using 4-bit QLoRA.")
        except Exception:  # noqa: BLE001
            print("[.] bitsandbytes unavailable — plain LoRA. (uv sync --extra gpu)")

    # Always load in bf16 (not fp32) — Gemma 4 E4B is ~16 GB in bf16; loading as
    # fp32 doubles that to ~32 GB and gets OOM-killed on a 31 GB laptop.
    # low_cpu_mem_usage streams the shards in instead of buffering a full copy.
    if not use_cuda:
        _warn_cpu_ram()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_cfg,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        device_map="auto" if use_cuda else None,
    )

    dataset = load_dataset("json", data_files=DATA, split="train")

    # Gemma 4's elastic (E-series) layers wrap each projection in a custom
    # `Gemma4ClippableLinear`; PEFT only attaches LoRA to the plain nn.Linear
    # inside it (`<proj>.linear`). Non-elastic models expose the projection as a
    # plain nn.Linear directly. Detect which and target accordingly.
    import torch.nn as nn
    proj = ["q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"]
    wrapped = False
    for name, mod in model.named_modules():
        if name.split(".")[-1] in proj:
            wrapped = not isinstance(mod, nn.Linear)
            break
    target_modules = [f"{p}.linear" for p in proj] if wrapped else proj
    print(f"[.] LoRA targets: {'wrapped (<proj>.linear)' if wrapped else 'plain <proj>'}")

    peft_cfg = LoraConfig(
        r=args.rank,
        lora_alpha=args.rank,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )

    sft_cfg = SFTConfig(
        output_dir=OUT_DIR,
        num_train_epochs=args.epochs,
        max_steps=2 if args.smoke else -1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        logging_steps=1,
        save_strategy="no" if args.smoke else "epoch",
        bf16=use_cuda,
        report_to=[],
        max_length=1024,
        # Trade compute for memory: recompute activations in backward instead of
        # storing them. Essential to fit a 4B base on a RAM-tight CPU box.
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_cfg,
        train_dataset=dataset,
        peft_config=peft_cfg,
        processing_class=tokenizer,
    )

    print(f"[.] Training on {len(dataset)} examples "
          f"({'smoke: 2 steps' if args.smoke else f'{args.epochs} epoch(s)'}) …")
    trainer.train()

    if not args.smoke:
        trainer.save_model(OUT_DIR)
        tokenizer.save_pretrained(OUT_DIR)
        print(f"[✓] LoRA adapter saved -> {OUT_DIR}")
        print("    Next: merge + export to GGUF, then `ollama create` to demo in Ollama.")
    else:
        print("[✓] Smoke test passed — the LoRA pipeline works end to end.")


if __name__ == "__main__":
    main()
