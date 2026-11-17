"""Write the Perspective in the Frontiers LaTeX template.

Usage: uv run python to_latex.py   (from paper/; writes frontiers/torres_perspective.tex
and frontiers/references.bib, and copies the figures as PDFs)

perspective.rsm stays the source. This script converts only the RSM constructs that the
paper uses: headings with labels, bold run-in leads, citations, references to sections,
figures and one labeled span, two figures with captions, the abstract with keywords, the
unnumbered statements, and the BibTeX entries under :references:.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "frontiers"
RUNNING_TITLE = "Three readings of group interactions"
STATEMENT_HEADINGS = {"Data availability": "Data Availability Statement",
                      "Supplementary material": "Supplementary Material",
                      "Funding": "Funding",
                      "Generative AI": "Generative AI Statement"}


def block(s, start, end):
    i = s.index(start) + len(start)
    return s[i:s.index(end, i)]


def inline(t):
    t = " ".join(t.split())
    t = re.sub(r":span:\{:label: ([\w-]+)\}\s*(.*?)::", r"\\phantomsection\\label{\1}\2", t)
    t = re.sub(r":ref:([\w-]+),([^:]+)::", r"\\hyperref[\1]{\2}", t)

    def ref(m):
        label, after = m.group(1), m.group(2)
        kind = "Figure" if label.startswith("fig-") else "Section"
        return f"{kind}~\\ref{{{label}}}{after}"
    t = re.sub(r":ref:([\w-]+)::([A-Z]?)", ref, t)
    # A citation that is the subject of the next verb takes the narrative form,
    # "Rommens et al. (2026) propose"; all others stay in parentheses.
    t = re.sub(r":cite:([\w,]+):: (propose|describe|calls|say|ask|argue)\b",
               r"\\citet{\1} \2", t)
    t = re.sub(r":cite:([\w,]+):: \(p\. (\d+)\)", r"\\citep[p.~\2]{\1}", t)
    t = re.sub(r":cite:([\w,]+)::", r"\\citep{\1}", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r'"([^"]+)"', r"``\1''", t)
    t = t.replace("&", r"\&")
    t = re.sub(r"(https://\S+?)(\.?)$", r"\\url{\1}\2", t)
    return t


def body(text):
    # Figure blocks hold blank lines, so they are taken out before the text is split
    # into paragraphs.
    figures = re.findall(r":figure: \{.*?\n::\n", text, flags=re.S)
    for n, fig in enumerate(figures):
        text = text.replace(fig, f"FIGURE{n}\n")
    out = []
    for part in re.split(r"\n\s*\n", text.strip()):
        if re.fullmatch(r"FIGURE\d+", part.strip()):
            part = figures[int(part.strip()[6:])]
        head = re.match(r"(#{2,3}) (.+?) \{\n((?:\s+:\S+:.*\n?)*)\}", part)
        if head:
            level = "section" if head.group(1) == "##" else "subsection"
            label = re.search(r":label: ([\w-]+)", head.group(3))
            out.append(f"\\{level}{{{head.group(2)}}}"
                       + (f"\\label{{{label.group(1)}}}" if label else ""))
            rest = part[head.end():].strip()
            if rest:
                out.append(inline(rest))
        elif part.startswith(":figure:"):
            label = re.search(r":label: ([\w-]+)", part).group(1)
            path = Path(re.search(r":path: (\S+)", part).group(1)).with_suffix(".pdf")
            caption = part.split(":caption:", 1)[1].rsplit("::", 1)[0]
            out.append("\\begin{figure}[h!]\n\\begin{center}\n"
                       f"\\includegraphics[width=\\textwidth]{{{path.name}}}\n"
                       "\\end{center}\n"
                       f"\\caption{{{inline(caption)}}}\\label{{{label}}}\n"
                       "\\end{figure}")
        elif part.strip() == "::":
            continue
        else:
            out.append(inline(part))
    return "\n\n".join(out)


def statements(text):
    out = []
    for part in re.split(r"\n\s*\n", text.strip()):
        m = re.match(r"\*\*(.+?)\.\*\* (.*)", part, flags=re.S)
        if m:
            out.append(f"\\section*{{{STATEMENT_HEADINGS[m.group(1)]}}}\n{inline(m.group(2))}")
    return "\n\n".join(out)


def frontiers_bib(bib):
    """Adjust the entries for Frontiers-Harvard.bst, which prints every @misc as
    "[Dataset]", has no url field, and lowercases titles."""
    bib = bib.strip().replace(" & ", r" \& ")
    # Titles keep the capitals that they have in the source (RFID, Akaike).
    bib = re.sub(r"title=\{(.*?)\},\n", lambda m: "title={{" + m.group(1) + "}},\n", bib,
                 flags=re.S)

    def preprint(m):
        entry = m.group(0)
        url = re.search(r"url=\{(.+?)\}", entry).group(1)
        entry = entry.replace("@misc{", "@unpublished{", 1)
        note = "note={{arXiv} [Preprint]. Available at: \\url{" + url + "}},"
        entry = re.sub(r"howpublished=\{arXiv \[Preprint\]\},\n\s*url=\{.+?\},",
                       lambda _: note, entry)
        return entry
    bib = re.sub(r"@misc\{\w+,(?:(?!\n\}).)*howpublished=\{arXiv \[Preprint\]\}.*?\n\}",
                 preprint, bib, flags=re.S)

    def working_paper(m):
        entry = m.group(0).replace("@misc{", "@techreport{", 1)
        how = re.search(r"howpublished=\{Working Paper (\d+), (.+?)\},", entry, flags=re.S)
        inst = " ".join(how.group(2).split())
        entry = entry.replace(how.group(0), f"type={{Working Paper}},\n  number={{{how.group(1)}}},"
                              f"\n  institution={{{inst}}},")
        return re.sub(r"\n\s*url=\{.+?\},", "", entry)
    bib = re.sub(r"@misc\{\w+,(?:(?!\n\}).)*howpublished=\{Working Paper.*?\n\}",
                 working_paper, bib, flags=re.S)
    return bib + "\n"


def word_count():
    subprocess.run(["just", "build"], cwd=HERE, check=True, capture_output=True)
    res = subprocess.run(["just", "count"], cwd=HERE, check=True, capture_output=True,
                         text=True)
    return int(res.stdout.strip().splitlines()[-1].split()[-1])


def main():
    s = (HERE / "perspective.rsm").read_text()
    title = re.match(r"# (.+?) \{", s).group(1)
    author = block(s, ":author: {", "}")
    name = re.search(r":name: (.+)", author).group(1).strip()
    affiliation = re.search(r":affiliation: (.+)", author).group(1).strip()
    email = re.search(r":email: (.+)", author).group(1).strip()
    keywords = re.search(r":keywords: \{(.+?)\}", s).group(1)
    abstract = block(s, ":abstract: {", "\n::\n").split("\n}\n", 1)[1]
    main_text = s[s.index("## Introduction"):s.index("## Statements")]
    stmts = block(s, ":nonum:\n}", ":references:")
    bib = block(s, ":references:", "\n::")
    words = word_count()

    OUT.mkdir(exist_ok=True)
    (OUT / "references.bib").write_text(frontiers_bib(bib))
    for fig in ("figure1", "figure2"):
        shutil.copy(HERE / "figs" / f"{fig}.pdf", OUT / f"{fig}.pdf")
    last = name.split()[-1]
    tex = rf"""% Generated by to_latex.py from perspective.rsm. Do not edit by hand.
\documentclass[utf8]{{FrontiersinHarvard}}
\usepackage{{url,hyperref,lineno,microtype,subcaption}}
\usepackage[onehalfspacing]{{setspace}}

\linenumbers

\def\keyFont{{\fontsize{{8}}{{11}}\helveticabold }}
\def\firstAuthorLast{{{last}}}
\def\Authors{{{name}\,$^{{*}}$}}
\def\Address{{{affiliation}}}
\def\corrAuthor{{{name}}}
\def\corrEmail{{{email}}}

\begin{{document}}
\onecolumn
\firstpage{{1}}

\title[{RUNNING_TITLE}]{{{title}}}

\author[\firstAuthorLast ]{{\Authors}}
\address{{}}
\correspondance{{}}

\extraAuth{{}}

\maketitle

\begin{{abstract}}

\section{{}}
{inline(abstract)}

\tiny
\keyFont{{ \section{{Keywords:}} {keywords}}}
\end{{abstract}}

\noindent Number of words in the main text: {words:,}. Number of figures and tables: 2.

{body(main_text)}

{statements(stmts)}

\bibliographystyle{{Frontiers-Harvard}}
\bibliography{{references}}

\end{{document}}
"""
    (OUT / "torres_perspective.tex").write_text(tex)
    print("wrote", OUT / "torres_perspective.tex", f"({words} words)")


if __name__ == "__main__":
    sys.exit(main())
