# Live-demo experiments — Open Source LLMs @ Code for Bielefeld

One small script per demo from the slides. Everything talks to a local
**Ollama** server, except the LoRA scripts which use a local Python ML stack.

## Setup (once)

```bash
# uv manages the single shared .venv for all experiments
uv sync                 # CPU install (works anywhere)
uv sync --extra gpu     # adds bitsandbytes for 4-bit QLoRA on an NVIDIA GPU
```

Run anything with `uv run`:

```bash
uv run python experiments/01_hook_chat.py
```

Make sure Ollama is up (`ollama serve`) and the models are pulled. Model tags
default to the slide names (`gemma4:e2b`, `gemma4:e4b`, `gemma4:12b`,
`qwen3.6:27b`) but every script honours env overrides, e.g.:

```bash
OLLAMA_SMALL=gemma2:2b OLLAMA_MID=gemma2:9b uv run python experiments/02_token_speed.py
```

Common env vars: `OLLAMA_HOST`, `OLLAMA_SMALL`, `OLLAMA_MID`, `OLLAMA_LARGE`,
`OLLAMA_VISION`, `OLLAMA_CODER` (see `_common.py`).

## The demos

| # | Script | Slide | What it shows |
|---|--------|-------|----------------|
| 0 | `01_hook_chat.py` | 02 Hook | A capable model answering in German, fully local, offline |
| 1 | `02_token_speed.py` | 06/07 | Same prompt at 3 sizes → tokens/s drops, quality rises |
| 1b| `03_ram_usage.py` | 06 | Live RAM footprint of loaded models (`--watch` to refresh) |
| 5 | `05_quantization_compare.py` | 10 | q4 vs q8 — near-identical answers, ~2× the RAM |
| 8 | `04_vision_json.py` | 13 | Photo of a form → structured JSON (multimodal, DSGVO-clean) |
| 8 | `06_coding_compare.py` | 13 | Gemma vs Qwen on a real coding task |
| 7 | `lora/` | 12 | Fine-tune a LoRA at home |

Run order for the talk roughly follows the numbers. `03_ram_usage.py` is the
"second terminal" during demo 1.

## LoRA fine-tuning (slide 12)

```bash
# 1. build the dataset (downloads a German instruction set from HF + an
#    Amtsdeutsch style seed) -> experiments/lora/data/train.jsonl
uv run python experiments/lora/prepare_dataset.py

# 2. authenticate once — Gemma 4 is gated (accept the license on its HF page)
uv run huggingface-cli login

# 3. prove the pipeline works (2 steps). Fast on GPU, slow on CPU.
uv run python experiments/lora/train_lora.py --smoke

# 4. real run — do this on a GPU / free Colab T4, not live on stage
uv run python experiments/lora/train_lora.py
# lighter base: BASE_MODEL=google/gemma-4-E2B-it uv run python experiments/lora/train_lora.py
```

Default base: **`google/gemma-4-E4B-it`** — the Gemma 4 E4B model from the
slides (gated; needs license acceptance + HF login).

Dataset: **FreedomIntelligence/alpaca-gpt4-deutsch** (real German instructions)
plus a small hand-written *Amtsdeutsch* style seed so the adapter has a
demo-able personality. The script writes chat-format JSONL.

For the talk, the slides suggest the **Unsloth** Colab notebook with a real
Gemma 4 base, then export to GGUF and `ollama create` to demo the result live.
`train_lora.py` is the portable "what actually happens" companion — it runs the
same LoRA/QLoRA recipe with plain transformers + peft + trl.

## Fallback

Every live demo should have a screen recording as backup (WiFi/hardware can
fail). These scripts are what you record.
