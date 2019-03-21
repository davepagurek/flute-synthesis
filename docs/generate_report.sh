#!/usr/bin/env bash
pandoc --filter pandoc-citeproc -f markdown+implicit_figures+raw_tex -s report.md -o report.pdf --toc
