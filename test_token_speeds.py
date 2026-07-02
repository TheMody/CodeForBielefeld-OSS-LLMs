import requests, time

MODELS = ["gemma4:e2b", "gemma4:e4b", "gemma4:12b"]
PROMPT = "Write a Python function that parses a German date string."

for model in MODELS:
    r = requests.post("http://localhost:11434/api/generate",
                      json={"model": model, "prompt": PROMPT, "stream": False})
    d = r.json()
    tps = d["eval_count"] / (d["eval_duration"] / 1e9)
    print(f"{model}: {tps:.1f} tokens/s, {d['eval_count']} tokens")