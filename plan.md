# Open Source LLMs — Presentation Plan

**Target length:** 30–45 min (+ Q&A)
**Setup:** Laptop with 16GB RAM, Ollama installed. Live demos throughout.
**Audience assumption:** technically interested, not necessarily ML experts (Code for Bielefeld) 

---

## 0. Hook / Intro (3 min)

- Opening live demo before any slides: `ollama run gemma4:e2b` and ask it something fun
  (in German — Gemma 4 supports 140+ languages). Point: **this runs entirely on this
  laptop, no cloud, no API key, no data leaves the room.**
- One slide: what "open source LLM" actually means (open weights vs. open data vs.
  open training code — most are "open weights"; licenses: Apache 2.0 (Qwen) vs.
  Gemma license vs. Llama license)
- Why care: privacy (DSGVO!), cost, offline, no vendor lock-in, fine-tunability
  — good angle for civic tech / Verwaltung

**Code:**
```bash
ollama run gemma4:e2b "Erkläre in 3 Sätzen, warum Bielefeld existiert."
```

---

## 1. The Landscape: Who's Who in Open Models (5 min)

- Quick map of the current families (mid-2026):
  - **Gemma 4** (Google): E2B / E4B / 12B Unified / 26B MoE / 31B — multimodal (text+image, 12B also audio), 256K context
  - **Qwen 3.6** (Alibaba): 27B dense — coding monster, Apache 2.0, 77.2% SWE-bench Verified
  - **DeepSeek / Llama / Mistral** — one line each *(TODO: pick current versions to mention)*
- Slide: timeline graphic "GPT-3 (closed, 175B, datacenter) → today (open, 4B, laptop)"
  — the compression of capability into small models is *the* story
- Killer stat to show: **Qwen3.6-27B beats its own 397B predecessor on coding benchmarks**
  → small + recent > big + old

**Media ideas:**
- Screenshot of the Ollama model library / Hugging Face open LLM leaderboard (live if WiFi works)
- Google's Gemma 4 announcement blog has good visuals

---

## 2. Live Demo Block 1: Small Models on This Laptop (8 min)

Goal: show *speed vs. RAM vs. quality* live, not just on slides.

- Run the same prompt on 2–3 model sizes, `--verbose` shows tokens/sec:

```bash
# Same prompt, increasing size — watch tokens/sec drop and quality rise
ollama run gemma4:e2b --verbose "Schreibe eine Python-Funktion, die prüft, ob ein Jahr ein Schaltjahr ist."
ollama run gemma4:e4b --verbose "..."
ollama run gemma4:12b --verbose "..."   # TODO: test beforehand if this fits in 16GB (q4 should, ~8GB)
```

- Show RAM usage live in a second terminal:

```bash
ollama ps        # shows loaded model + memory footprint
```

- **The wall:** try `ollama pull qwen3.6:27b` → show that Q4 weights alone are ~16GB
  → doesn't fit → perfect segue to quantization + "bigger hardware" section
- Multimodal teaser: drop an image into Gemma 4 (Ollama supports image input):

```bash
ollama run gemma4:e4b "Was ist auf diesem Bild zu sehen?" ./bielefeld-rathaus.jpg
```

**Prepare:** pre-pull all models (demo WiFi rule #1), pre-test the exact prompts,
have screen-recorded fallback videos of every demo.

---

## 3. The Numbers: Token Speed vs. RAM vs. Quality (5 min)

- One comparison table/chart (build from your own measurements — much more credible
  than benchmark screenshots):

| Model | Params | Quant | RAM | Tokens/s (this laptop) | Quality (task score) |
|---|---|---|---|---|---|
| gemma4:e2b | 2.3B | Q4 | ~3GB | *measure* | *rate* |
| gemma4:e4b | 4B | Q4 | ~5GB | *measure* | *rate* |
| gemma4:12b | 12B | Q4 | ~8GB | *measure* | *rate* |
| qwen3.6:27b | 27B | Q4 | ~17GB | ❌ (doesn't fit) | — |
| qwen3.6:27b (cloud/workstation) | 27B | Q8/FP16 | 30–60GB | *from rented GPU?* | *rate* |

- Small benchmark script to generate the numbers (run beforehand, show the script live):

```python
import requests, time

MODELS = ["gemma4:e2b", "gemma4:e4b", "gemma4:12b"]
PROMPT = "Write a Python function that parses a German date string."

for model in MODELS:
    r = requests.post("http://localhost:11434/api/generate",
                      json={"model": model, "prompt": PROMPT, "stream": False})
    d = r.json()
    tps = d["eval_count"] / (d["eval_duration"] / 1e9)
    print(f"{model}: {tps:.1f} tokens/s, {d['eval_count']} tokens")
```

- Rule of thumb slide: **RAM ≈ params × bytes-per-weight + context overhead**
  (FP16 = 2 bytes/param, Q4 ≈ 0.5 bytes/param → 27B model: 54GB FP16 vs. ~15GB Q4)
- → segue: "so what hardware buys you what speed?" → next section

---

## 4. Hardware: What Does Speed Cost? (5 min)

**The one formula that explains everything:**

> **tokens/s ≈ memory bandwidth ÷ model size in bytes**

LLM inference is *memory-bandwidth-bound*, not compute-bound — every generated token
reads all weights once. This single fact explains the whole hardware market:

- CPU (dual-channel DDR5, ~100GB/s) → a Q4 4B model (~2.5GB): ~40 t/s ✅, a Q4 27B (~16GB): ~6 t/s 😴
- GPU (GDDR6X/7, 900–1800GB/s) → 10–18× faster... *if the model fits in VRAM*
- Unified memory (Apple, AMD Strix Halo) → middle bandwidth, but *huge* capacity
  → runs models no consumer GPU can hold

**The buyer's table (prices mid-2026, approx. — TODO: refresh before the talk):**

| Option | Memory | Bandwidth | Price | Sweet spot | Qwen3.6-27B Q4? |
|---|---|---|---|---|---|
| This laptop (CPU, 16GB) | 16GB shared | ~100GB/s | owned 🙂 | ≤4B models | ❌ |
| Used RTX 3090 | 24GB VRAM | 936GB/s | ~€600–700 | **best t/s per €** — up to ~30B Q4 | ✅ fast |
| RTX 4090 | 24GB VRAM | 1,008GB/s | ~€1,800 | same fit as 3090, faster | ✅ fast |
| RTX 5090 | 32GB VRAM | 1,792GB/s | ~€2,600–3,500 | 70B Q4 at 45+ t/s | ✅ very fast |
| Ryzen AI Max+ 395 mini-PC | up to 128GB unified | 256GB/s | ~€1,500–2,000 | *big* models slowly (70B @ ~5–15 t/s) | ✅ medium |
| Mac Studio (M4 Max/M3 Ultra) | up to 512GB unified | 546–819GB/s | €2,500–5,000+ | 70B @ 20–30 t/s, zero setup | ✅ fast |
| Rented GPU (RunPod/vast.ai) | any | any | ~€0.30–0.70/h (3090/4090) | trying before buying | ✅ |

- Talking points:
  - **Used RTX 3090 is the community favorite:** same 24GB VRAM as a 4090 at ~⅓ the
    price — the "Geheimtipp" for a home LLM box (~€1,200 total build)
  - **The VRAM cliff:** a model that doesn't fit in VRAM falls back to system RAM and
    speed drops off a cliff — capacity gates *what* you can run, bandwidth gates *how fast*
  - **CPU is fine for small models!** Gemma 4 E2B/E4B run pleasantly on any modern
    laptop — that's the actual revolution, not the €3,000 GPU
  - Renting vs. buying break-even: at ~€0.50/h, a used 3090 pays for itself after
    ~1,300 hours *(TODO: check figures)*
- Live tie-in: your section-3 measurements ARE the CPU row of this table — reference back
- Optional demo: `ollama ps` shows `100% CPU` on your laptop; screenshot/recording of
  the same command on a GPU box showing `100% GPU` + the t/s difference

**Media ideas:**
- Bar chart: tokens/s per € across the table rows (one glance, very shareable)
- Photo: used RTX 3090 eBay listing next to a Mac Studio product page
- Hardware-corner.net / r/LocalLLaMA benchmark threads for real-world t/s numbers

---

## 5. Quantization — Why Your Laptop Can Do This At All (6 min)

- Intuition first: weights are just numbers; FP16 → INT4 = storing them sloppier.
  Analogy: JPEG for neural networks — lossy, but you barely notice.
- Visual: same image at decreasing JPEG quality next to model benchmark scores at
  decreasing quant levels (Q8 → Q4 → Q2). Q4 is the sweet spot; Q2 visibly degrades.
- Show it live — same model, two quants:

```bash
ollama pull gemma4:e2b-it-q4_K_M   # and a q8 variant
# same prompt on both → compare speed, RAM, and (usually) barely different output
```

- Optional demo if time: an *over*-quantized model (Q2) giving noticeably worse answers
  — degradation is more memorable than a chart
- Mention GGUF format, llama.cpp as the engine underneath Ollama (one slide, no depth)

**Media ideas:**
- 3Blue1Brown "How LLMs work" clips for the "weights are just numbers" intuition
- Chart: perplexity/benchmark vs. quant level from llama.cpp docs

---

## 6. Inference vs. Training — Why You Can Run But Not Train (6 min)

**The core math slide of the talk.** For a 4B parameter model:

| | Memory needed | On your laptop? |
|---|---|---|
| Inference Q4 | ~2.5GB (weights, 4-bit) | ✅ easy |
| Inference FP16 | ~8GB | ✅ just |
| **Full training** | weights FP16 (8GB) + gradients (8GB) + Adam optimizer states (16GB) + activations (≫) ≈ **50GB+** | ❌ |
| Training a 27B | ~350GB+ → multi-GPU cluster | ❌❌ |

- Key insights to land:
  1. Training needs **~10–20× the memory** of quantized inference (gradients +
     optimizer states + activations for backprop)
  2. Training can't be (aggressively) quantized — gradient updates need precision;
     tiny updates vanish in 4-bit
  3. It's also **compute**: Gemma-class pretraining = thousands of GPUs × weeks;
     your laptop would need centuries *(TODO: fun back-of-envelope calc, e.g.
     "training Gemma 4 on this laptop ≈ X years")*
- Nice framing: inference = *reading* the book, training = *writing* it

**Media ideas:**
- Photo of a GPU datacenter vs. your laptop side by side
- Diagram: memory breakdown bar chart (weights / gradients / optimizer / activations)

---

## 7. The Loophole: Fine-Tuning with LoRA (5 min)

- Bridge from previous section: "…but there's a trick to *customize* models at home"
- LoRA in one diagram: freeze the 4B weights, train two tiny matrices (~0.1–1% of
  params) on the side. QLoRA = do it on top of a *quantized* base model
  → fine-tuning Gemma 4 E4B fits in ~8–12GB
- Unsloth has official Gemma 4 support with free Colab notebooks — realistic demo path:
  **pre-train a LoRA before the talk, show the training notebook briefly, then demo
  the result live in Ollama** (don't train live — too slow, too fragile)
- Fun dataset idea for the demo LoRA: make Gemma answer in Bielefelder Platt /
  official Amtsdeutsch / Code-for-Bielefeld style *(TODO: decide + build dataset,
  ~100–500 examples is enough for a style LoRA)*

```python
# Unsloth QLoRA sketch (runs on free Colab T4)
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/gemma-4-e4b-it", load_in_4bit=True)
model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16)
# ... train on your dataset, export GGUF, `ollama create` → demo
```

- Honest slide: what LoRA can (style, format, domain vocabulary) and can't
  (new knowledge at scale, new capabilities) do

---

## 8. Capabilities: Not All Open Models Are Equal (5 min)

Message: **pick the model for the task, not the biggest one.**

- **Gemma 4 = the multimodal generalist:** text + images (12B Unified: + audio),
  140+ languages, strong German
  - Live: photo of a form/Fahrplan/handwritten note → have Gemma extract data as JSON
  - Civic-tech hook: "scan a paper form into structured data, fully local, DSGVO-clean"
- **Qwen 3.6 27B = the coder:** text-only focus, 77.2% SWE-bench Verified,
  Terminal-Bench on par with frontier closed models
  - Demo (recorded from bigger hardware, or via API): a real coding task both models
    attempt — Gemma E4B fails/struggles, Qwen nails it
- One slide honorable mentions: *(TODO: pick)* e.g. Whisper (speech→text, runs
  anywhere), a small embedding model (local RAG teaser), DeepSeek-R1-style reasoning
- Optional if time: open model plugged into a coding agent (Qwen + Cline/aider) —
  "local GitHub Copilot"

---

## 9. Wrap-Up (2 min)

- Takeaways:
  1. Capable LLMs run on normal laptops **today** — quantization makes it possible
  2. Inference is cheap, training is astronomical, **LoRA is the middle path**
  3. Model choice = task fit: multimodal (Gemma) vs. coding (Qwen) vs. size vs. speed
- "Try it yourself" slide: `ollama.com` → one command → running in 5 minutes
- Idea for Code for Bielefeld: a local-LLM project? (document processing, local RAG
  over Ratsinformationssystem?)

---

## TODO / Prep Checklist

- [ ] Pre-pull all models: `gemma4:e2b`, `gemma4:e4b`, `gemma4:12b`, quant variants
- [ ] Verify `gemma4:12b` actually runs OK in 16GB (close browsers!)
- [ ] Run benchmark script, fill in the real numbers for section 3 table
- [ ] Decide bigger-hardware story: rent a GPU for real Qwen 3.6 numbers, or use published benchmarks?
- [ ] Refresh hardware prices in section 4 shortly before the talk (GPU street prices move fast)
- [ ] Check rent-vs-buy break-even math (€0.50/h vs. used 3090 build cost)
- [ ] Build + train the demo LoRA (dataset, Colab run, export to Ollama)
- [ ] Pick demo images for multimodal (form, photo, handwriting)
- [ ] Screen-record every live demo as fallback
- [ ] Fun back-of-envelope: "training Gemma 4 on this laptop = X years"
- [ ] Verify: is Qwen 3.6 27B really text-only? (some sources list MMMU scores → suggests vision?)
- [ ] Licenses slide: double-check current Gemma license terms vs. Apache 2.0

## Sources

- [Google: Gemma 4 announcement](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/)
- [Unsloth: Gemma 4 docs](https://unsloth.ai/docs/models/gemma-4)
- [Ollama library: gemma4](https://ollama.com/library/gemma4:e4b)
- [The Decoder: Qwen3.6-27B beats larger predecessor](https://the-decoder.com/qwen3-6-27b-beats-much-larger-predecessor-on-most-coding-benchmarks/)
- [Qwen 3.6 27B benchmarks](https://llm-stats.com/models/qwen3.6-27b)
- [Qwen 3.6 27B as local coding model](https://ai.rs/ai-developer/qwen-3-6-27b-local-coding-model)
- [LLM GPU buyer's guide: VRAM per dollar tier list (Apr 2026)](https://corelab.tech/llmgpu/)
- [Local LLM GPU guide: RTX 5090/4090/3090 compared](https://medium.com/codex/best-gpus-for-running-local-llms-in-2026-what-actually-works-292f27a99f04)
- [Ryzen AI Max+ 395 for local LLMs: 2026 reality check](https://www.modemguides.com/blogs/ai-infrastructure/ryzen-ai-max-395-local-llm-reality-check)
- [Pinggy: picking hardware to run LLMs locally in 2026](https://pinggy.io/blog/best_hardware_for_self_hosting_local_llms/)
