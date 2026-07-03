"""Demo / Slide 13 — Multimodal: photo of a paper form -> structured JSON, local.

The civic-tech hook: "scan a paper form into structured data, fully local,
DSGVO-clean." Uses a multimodal Gemma model. If you don't pass an image it
generates a synthetic German registration form so the demo works offline.

    python experiments/04_vision_json.py                       # synthetic form
    python experiments/04_vision_json.py assets/rathaus.jpg    # your own image
"""
from __future__ import annotations

import base64
import os
import sys

from _common import MODEL_VISION, check_server, ensure_model, generate

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
SAMPLE = os.path.join(ASSETS, "anmeldeformular.png")

PROMPT = (
    "Dies ist ein ausgefülltes deutsches Formular. Extrahiere alle Felder als "
    "JSON mit den Schlüsseln in snake_case. Antworte NUR mit gültigem JSON."
)


def make_sample_form(path: str) -> None:
    """Render a fake 'Anmeldung' form so the vision demo is self-contained."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (760, 520), "white")
    d = ImageDraw.Draw(img)
    try:
        title_f = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        f = ImageFont.truetype("DejaVuSans.ttf", 20)
    except OSError:
        title_f = f = ImageFont.load_default()

    d.text((40, 30), "Stadt Bielefeld — Anmeldung Wohnsitz", fill="black", font=title_f)
    d.line((40, 72, 720, 72), fill="black", width=2)

    fields = [
        ("Nachname", "Musterfrau"),
        ("Vorname", "Erika"),
        ("Geburtsdatum", "14.03.1985"),
        ("Straße, Hausnr.", "Sparrenstraße 12"),
        ("PLZ, Ort", "33602 Bielefeld"),
        ("Einzugsdatum", "01.07.2026"),
        ("Staatsangehörigkeit", "deutsch"),
    ]
    y = 110
    for label, value in fields:
        d.text((40, y), f"{label}:", fill="black", font=f)
        d.text((320, y), value, fill="#0b3d91", font=f)
        d.line((315, y + 26, 720, y + 26), fill="#999", width=1)
        y += 52

    os.makedirs(ASSETS, exist_ok=True)
    img.save(path)


def main() -> None:
    check_server()

    image_path = sys.argv[1] if len(sys.argv) > 1 else SAMPLE
    if image_path == SAMPLE and not os.path.exists(SAMPLE):
        print("[.] No image given — generating a synthetic Anmeldeformular …")
        make_sample_form(SAMPLE)
    if not os.path.exists(image_path):
        sys.exit(f"[!] Image not found: {image_path}")

    ensure_model(MODEL_VISION)
    with open(image_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()

    print(f"\n$ ollama run {MODEL_VISION}  (image: {image_path})")
    print(f">>> {PROMPT}\n")
    generate(MODEL_VISION, PROMPT, images=[b64], stream=True)
    print("\n# text + image in -> structured data out, 100% on this laptop")


if __name__ == "__main__":
    main()
