#!/bin/sh
# Compile the Frontiers LaTeX file: pdflatex, bibtex, then pdflatex twice for references.
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode torres_perspective.tex >/dev/null || true
bibtex torres_perspective
pdflatex -interaction=nonstopmode torres_perspective.tex >/dev/null || true
pdflatex -interaction=nonstopmode -halt-on-error torres_perspective.tex
