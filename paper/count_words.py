"""Count main-text words in the rendered Perspective, following Frontiers' rule:
main body text and in-text citations count; abstract, headings, captions,
statements and references do not."""
import re
import sys
from bs4 import BeautifulSoup

BODY = ["sec-intro", "sec-argument", "sec-study", "sec-recommendations"]

def words(text):
    # A word is any run of non-space characters that has a letter or digit,
    # so "(Rommens", "2026)." and "2,781" each count once and lone punctuation does not.
    return [w for w in text.split() if re.search(r"\w", w)]

soup = BeautifulSoup(open(sys.argv[1], encoding="utf-8").read(), "html.parser")
total = total_runin = 0
for sid in BODY:
    sec = soup.find("section", id=sid)
    for fig in sec.find_all("figure"):
        fig.decompose()
    # Only <p> elements hold prose; the rest of each section is editor UI
    # (buttons, icons, menus) and the h2 heading.
    paras = sec.find_all("p")
    n = sum(len(words(p.get_text(" "))) for p in paras)
    runin = sum(len(words(s.get_text(" "))) for p in paras
                for s in p.find_all(["strong", "b"]) if p.contents and
                p.find(["strong", "b"]) is s)
    heading = sec.find(["h2", "h3"]).get_text(" ", strip=True)
    print(f"{heading:40s} paragraphs={len(paras):3d} words={n:5d} run-in bold leads={runin}")
    total += n
    total_runin += runin
print(f"TOTAL main text words: {total}")
print(f"TOTAL without bold run-in paragraph leads: {total - total_runin}")
