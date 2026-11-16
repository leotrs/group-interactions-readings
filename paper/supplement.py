"""Build the three supplementary files as PDFs (Frontiers takes PDF data sheets).

Usage: uv run python supplement.py   (from paper/; writes supplement/S1.pdf to S3.pdf)
The Markdown sources stay where the code is. The web-only <picture> block in S2, which
switches images for dark mode, becomes a plain image here.
"""

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {"S1": ROOT / "study/SIMULATION.md", "S2": ROOT / "study/supplement.md",
         "S3": ROOT / "remedy/SUPPLEMENT.md"}
OUT = Path(__file__).resolve().parent / "supplement"


def plain_images(text, base):
    def repl(m):
        src = re.search(r'<img src="([^"]+)"', m.group(0)).group(1)
        return f"![]({(base / src).resolve()}){{width=100%}}"
    return re.sub(r"<picture>.*?</picture>", repl, text, flags=re.S)


def main():
    OUT.mkdir(exist_ok=True)
    for name, src in FILES.items():
        text = plain_images(src.read_text(), src.parent)
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
            tmp.write(text)
        subprocess.run(["pandoc", tmp.name, "-o", str(OUT / f"{name}.pdf"),
                        "--pdf-engine=xelatex", "-V", "geometry:margin=2cm",
                        "-V", "fontsize=10pt", "-V", "mainfont=Helvetica Neue",
                        "-V", "colorlinks=true"], check=True)
        print("wrote", OUT / f"{name}.pdf")


if __name__ == "__main__":
    main()
