"""Builds RSM317_GroupAssignment1.ipynb from the percent-format cell files in planning/cells."""
import re
from pathlib import Path

import nbformat

here = Path(__file__).parent
cells = []
for cell_file in sorted((here / "cells").glob("*.py")):
    parts = re.split(r"^# %%(.*)$", cell_file.read_text(encoding="utf-8"), flags=re.M)
    for tag, body in zip(parts[1::2], parts[2::2]):
        body = body.strip("\n")
        if "[markdown]" in tag:
            lines = [line[2:] if line.startswith("# ") else line.lstrip("#") for line in body.splitlines()]
            cells.append(nbformat.v4.new_markdown_cell("\n".join(lines)))
        else:
            cells.append(nbformat.v4.new_code_cell(body))

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbformat.write(nb, here.parent / "RSM317_GroupAssignment1.ipynb")
print(f"Wrote notebook with {len(cells)} cells")
