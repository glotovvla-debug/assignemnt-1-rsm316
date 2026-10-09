# %% [markdown]
# ## 1. Loading the filings
#
# We loop over all `*.html` files in the current directory (no file names are typed into the code).
# The company name is taken from the file name, e.g. `Coca-Cola_10-K.html` → `Coca-Cola`.

# %%
import re
import html
import time
import unicodedata
from pathlib import Path
from collections import Counter
from datetime import datetime
from functools import lru_cache

import pandas as pd

current_directory = Path.cwd()

raw_html = {}  # company name -> raw HTML text
for html_file in sorted(current_directory.glob("*.html")):
    with html_file.open("r", encoding="utf-8") as file:
        content = file.read()
    company = html_file.stem.replace("_10-K", "").replace("_", " ")
    raw_html[company] = content
    print(f"Loaded {html_file.name}: {len(content):,} characters")

print(f"\n{len(raw_html)} filings loaded")
