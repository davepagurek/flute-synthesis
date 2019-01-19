#!/usr/bin/env bash
pandoc --filter pandoc-citeproc -f markdown-implicit_figures -s report.md -o report.pdf --toc
