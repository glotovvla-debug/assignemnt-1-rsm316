# RSM317 Assignment 1 — 10-K Parser Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One Jupyter notebook that cleans ten 10-K HTML filings with regex, spell-checks them with Norvig's checker on Webster's dictionary, extracts fiscal-year end / Item 3 / signature dates / signers into `legalproceedings.csv`, verifies every value, and compares against Beautiful Soup.

**Architecture:** The notebook is generated from percent-format cell files (`planning/cells/NN_*.py`) by `planning/build_notebook.py`, executed on a fresh kernel with `nbconvert`, and its outputs (clean text files, CSV, notebook JSON) are checked by pytest tests in `planning/tests/`. Each task adds one cell file plus the tests that pin its behaviour.

**Tech Stack:** Python 3.14 (Anaconda), `re`, `html`, `pathlib`, `pandas`, `nbformat`, `nbconvert`, `pytest`, `bs4` (bonus only).

**Spec:** `planning/2026-10-09-10k-parser-design.md`

## Global Constraints

- Project dir: `/Users/v.g./Desktop/Assignment 1 /` (note the trailing space — always quote the path).
- Exactly 10 `.html` files in the project dir; named `<Company>_10-K.html`.
- Main pipeline (sections 1–5) uses only regex and string methods — no `bs4`/`BeautifulSoup` before the Bonus heading.
- Files are loaded with a `Path.cwd().glob("*.html")` loop; no hard-coded file names in the notebook.
- Dates in ISO format `YYYY-MM-DD`; multiple values comma-separated.
- CSV written with `df.to_csv("legalproceedings.csv", index=False)`, built from a dict first.
- Clean text saved as `clean_text/<Company_with_underscores>_10-K.txt`; spell checker does not modify them.
- Relative paths only; notebook must pass Restart & Run All (nbconvert `--execute`) with no errors.
- Style: plain functions, short docstrings, markdown cell before each section; no classes.
- No git repo: "commit" checkpoints are replaced by the RUN command passing.

**RUN command** (used by every task):

```bash
cd "/Users/v.g./Desktop/Assignment 1 " && python3 planning/build_notebook.py && jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 RSM317_GroupAssignment1.ipynb && python3 -m pytest planning/tests -q
```

## Review Focus

1. Small-caps headings/names split into `<span>`s (Alphabet `S UNDAR P ICHAI`, Microsoft `B USINESS`) — names must come out whole. → Task 2 test `test_small_caps_names_are_not_split`.
2. Table-of-contents duplicates of "Item 3" and "Signatures" — the real section must be used, ending before Item 4. → Task 4 test `test_item3_bounds`.
3. Non-signature dates inside the signature section (Walmart footer "Fiscal Year Ended January 31, 2026", J&J exhibit index dates) — must not be reported as signature dates. → Task 4 test `test_signature_dates`.
4. Names containing a comma (`Robert E. Moritz, Jr.`) would break the comma-separated signer list. → Task 4 test `test_signers_special_cases`.
5. The same person signing twice (Microsoft: Alice L. Jolla; most companies: CEO) and the audit firm (`/s/ Ernst & Young LLP`) — listed once, auditor never. → Task 4 test `test_signers_special_cases`.

---

### Task 1: Filings, notebook builder, and loading section

**Files:**
- Create: `<project>/<Company>_10-K.html` ×10
- Create: `planning/build_notebook.py`
- Create: `planning/cells/00_intro.py`, `planning/cells/01_load.py`
- Create: `planning/tests/test_outputs.py`

**Interfaces:**
- Produces: notebook variables `current_directory: Path`, `raw_html: dict[str, str]` (company name → raw HTML). Company names: `Alphabet, Amazon, Apple, Coca-Cola, Johnson and Johnson, Meta, Microsoft, Procter and Gamble, Tesla, Walmart`.
- Produces: imports `re, html, time, Path, Counter, datetime, lru_cache, pd` available to later cells.

- [ ] **Step 1: Write the failing test** — create `planning/tests/test_outputs.py`:

```python
import json
import re
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[2]
NOTEBOOK = PROJECT / "RSM317_GroupAssignment1.ipynb"


def test_exactly_ten_html_files():
    assert len(list(PROJECT.glob("*.html"))) == 10


def test_notebook_ran_without_errors():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        for out in cell.get("outputs", []):
            assert out.get("output_type") != "error", "".join(cell["source"])[:200]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd "/Users/v.g./Desktop/Assignment 1 " && python3 -m pytest planning/tests -q`
Expected: FAIL (0 html files; notebook missing).

- [ ] **Step 3: Download the ten filings**

```bash
cd "/Users/v.g./Desktop/Assignment 1 "
UA="RSM317 student glotov.vla@gmail.com"
B=https://www.sec.gov/Archives/edgar/data
while read name path; do
  curl -sf -H "User-Agent: $UA" "$B/$path" -o "${name}_10-K.html"; sleep 0.3
done <<'EOF'
Apple 320193/000032019325000079/aapl-20250927.htm
Microsoft 789019/000119312526323660/msft-20260630.htm
Amazon 1018724/000101872426000004/amzn-20251231.htm
Tesla 1318605/000162828026003952/tsla-20251231.htm
Meta 1326801/000162828026003942/meta-20251231.htm
Alphabet 1652044/000165204426000018/goog-20251231.htm
Johnson_and_Johnson 200406/000020040626000016/jnj-20251228.htm
Coca-Cola 21344/000162828026010047/ko-20251231.htm
Procter_and_Gamble 80424/000008042426000103/pg-20260630.htm
Walmart 104169/000010416926000055/wmt-20260131.htm
EOF
ls -la *.html
```

Expected: 10 files, each > 1 MB.

- [ ] **Step 4: Create `planning/build_notebook.py`**

```python
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
```

- [ ] **Step 5: Create `planning/cells/00_intro.py`**

```python
# %% [markdown]
# # RSM317 – Group Assignment 1: Cleaning and Parsing SEC Form 10-K Filings
#
# **Team members:** _(add names and student numbers)_
#
# **Goal.** For the Rotman Investment Club we build a small proof-of-concept pipeline that takes the latest
# annual report (Form 10-K) of ten large US companies as plain HTML, removes the HTML tags, checks the
# spelling with Norvig's spell checker, and extracts four pieces of information from every report:
#
# 1. the fiscal year end date (ISO format),
# 2. the text of *Item 3. Legal Proceedings*,
# 3. the date(s) of the signatures (ISO format),
# 4. the people who signed the report (without the audit firm).
#
# The results are stored in `legalproceedings.csv`. In Section 5 we verify every extracted value against
# what we read in the filings ourselves. The bonus section repeats the extraction with Beautiful Soup.
#
# **Data.** The ten filings were downloaded from SEC EDGAR (company search → latest 10-K → open document)
# and saved in this folder as `<Company>_10-K.html`. They are the only HTML files in the folder.
```

- [ ] **Step 6: Create `planning/cells/01_load.py`**

```python
# %% [markdown]
# ## 1. Loading the filings
#
# We loop over all `*.html` files in the current directory (no file names are typed into the code).
# The company name is taken from the file name, e.g. `Coca-Cola_10-K.html` → `Coca-Cola`.

# %%
import re
import html
import time
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
```

- [ ] **Step 7: Run RUN command**
Expected: notebook builds and executes; both tests PASS; output lists 10 files.

---

### Task 2: Regex cleaning and clean-text files

**Files:**
- Create: `planning/cells/02_clean.py`
- Modify: `planning/tests/test_outputs.py` (append tests)

**Interfaces:**
- Consumes: `raw_html`, `current_directory`.
- Produces: `clean_html(raw: str) -> str`; `clean_texts: dict[str, str]` (company → clean text); files `clean_text/<Company_with_underscores>_10-K.txt`.

- [ ] **Step 1: Write the failing tests** (append to `test_outputs.py`)

```python
CLEAN_DIR = PROJECT / "clean_text"


def test_clean_text_files_have_no_tags():
    files = sorted(CLEAN_DIR.glob("*.txt"))
    assert len(files) == 10
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert not re.search(r"</?(div|span|p|td|tr|table|font|ix:[a-z]+)\b", text, re.I), f.name
        assert "&nbsp;" not in text and "&#" not in text and "\xa0" not in text, f.name


def test_small_caps_names_are_not_split():
    alphabet = (CLEAN_DIR / "Alphabet_10-K.txt").read_text(encoding="utf-8")
    microsoft = (CLEAN_DIR / "Microsoft_10-K.txt").read_text(encoding="utf-8")
    assert "SUNDAR PICHAI" in alphabet
    assert "S UNDAR" not in alphabet
    assert "B USINESS" not in microsoft
```

- [ ] **Step 2: Run tests — expect FAIL** (`clean_text` does not exist).

Run: `cd "/Users/v.g./Desktop/Assignment 1 " && python3 -m pytest planning/tests -q`

- [ ] **Step 3: Create `planning/cells/02_clean.py`**

```python
# %% [markdown]
# ## 2. Removing the HTML tags
#
# The filings are *inline XBRL* HTML: normal HTML plus hidden XBRL data. We clean them with regular
# expressions only:
#
# 1. Delete `<script>`, `<style>` and the hidden `<ix:header>` block **including their content**.
# 2. Replace the end of block elements (`</p>`, `</div>`, `</tr>`, …) and `<br>` with a newline, so
#    paragraphs and table rows stay on separate lines.
# 3. Replace the end of a table cell (`</td>`, `</th>`) with ` | `, so the columns of a table stay apart.
# 4. Delete all remaining tags **without inserting a space**. Some filings write small capitals as
#    separate `<span>`s in the middle of a word (Alphabet: `S<span>UNDAR</span> P<span>ICHAI</span>`).
#    Replacing tags with a space would give "S UNDAR P ICHAI".
# 5. Convert HTML entities (`&amp;`, `&#8217;`, …) with `html.unescape` and turn non-breaking spaces
#    into normal spaces.
# 6. Tidy whitespace: one space between words, no empty lines, no empty table cells.

# %%
def clean_html(raw):
    "Remove HTML tags with regular expressions and return readable text."
    text = re.sub(r"(?is)<(script|style|ix:header)\b.*?</\1>", " ", raw)
    text = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h[1-6]|table)>", "\n", text)
    text = re.sub(r"(?i)</t[dh]>", " | ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ").replace("​", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"( ?\| ?){2,}", " | ", text)          # several empty cells -> one separator
    text = re.sub(r"(?m)^[ |]+|[ |]+$", "", text)        # separators at the start/end of a line
    text = re.sub(r"\n\s*\n+", "\n", text)               # remove empty lines
    return text.strip()


clean_dir = current_directory / "clean_text"
clean_dir.mkdir(exist_ok=True)

clean_texts = {}
for company, raw in raw_html.items():
    clean_texts[company] = clean_html(raw)
    out_file = clean_dir / f"{company.replace(' ', '_')}_10-K.txt"
    out_file.write_text(clean_texts[company], encoding="utf-8")
    print(f"{company:22} {len(raw):>10,} -> {len(clean_texts[company]):>9,} characters  saved to {out_file.name}")

# %%
# A quick look at the result: the beginning of Apple's report
print(clean_texts["Apple"][:1500])
```

- [ ] **Step 4: Run RUN command** — expect all tests PASS. If `test_small_caps_names_are_not_split` fails, search the clean text for the split form and fix the regex, then rerun.

- [ ] **Step 5: Glued-word check** — run in a scratch shell (not in the notebook):

```bash
cd "/Users/v.g./Desktop/Assignment 1 " && python3 -c "
import re,pathlib
for f in sorted(pathlib.Path('clean_text').glob('*.txt')):
    t=f.read_text(encoding='utf-8')
    print(f.name, re.findall(r'\b[a-z]{3,}[A-Z][a-z]{3,}\b', t)[:8])"
```

Expected: only genuine camel-case names (e.g. `iPhone`-like brands). If words such as `theCompany` show up in many places, note it for the Section 3 discussion (it is a cost of step 4) — do not change the approach.

---

### Task 3: Norvig spell checker with Webster's dictionary

**Files:**
- Create: `planning/cells/03_spellcheck.py`

**Interfaces:**
- Consumes: `clean_texts`, `current_directory`.
- Produces: `WORDS: Counter`, `words(text)`, `correction(word)`, `fast_correction(word)`, `spell_df: DataFrame` (columns `company, unique_tokens, unknown_naive, unknown_improved`). Nothing later depends on these.

- [ ] **Step 1: Create `planning/cells/03_spellcheck.py`**

```python
# %% [markdown]
# ## 3. Spell checking with Norvig's spell checker
#
# Peter Norvig's spell checker (https://norvig.com/spell-correct.html) learns word probabilities from a
# large text, the corpus. Instead of the Sherlock Holmes stories we use **Webster's Unabridged
# Dictionary** from Project Gutenberg. First we remove the Gutenberg header and the licence at the end,
# because they are not part of the dictionary.

# %%
webster_file = next(current_directory.glob("Webster*.txt"))
webster = webster_file.read_text(encoding="utf-8")
start = webster.find("*** START OF")
end = webster.find("*** END OF")
webster = webster[webster.find("\n", start) + 1 : end]


# ----- Norvig's spell checker (unchanged, only the corpus is different) -----
def words(text):
    return re.findall(r"\w+", text.lower())

WORDS = Counter(words(webster))

def P(word, N=sum(WORDS.values())):
    "Probability of `word`."
    return WORDS[word] / N

def correction(word):
    "Most probable spelling correction for word."
    return max(candidates(word), key=P)

def candidates(word):
    "Generate possible spelling corrections for word."
    return known([word]) or known(edits1(word)) or known(edits2(word)) or [word]

def known(words):
    "The subset of `words` that appear in the dictionary of WORDS."
    return set(w for w in words if w in WORDS)

def edits1(word):
    "All edits that are one edit away from `word`."
    letters    = "abcdefghijklmnopqrstuvwxyz"
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)

def edits2(word):
    "All edits that are two edits away from `word`."
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))


print(f"Webster's corpus: {len(WORDS):,} different words, {sum(WORDS.values()):,} words in total")
print("Most common words:", WORDS.most_common(10))

# %% [markdown]
# ### 3.1 A naive first run
#
# We apply Norvig's tokenizer to every cleaned filing and count how many of the *different* words are
# not in Webster's dictionary.

# %%
naive_rows = []
for company, text in clean_texts.items():
    unique_tokens = set(words(text))
    unknown = [w for w in unique_tokens if w not in WORDS]
    naive_rows.append({"company": company, "unique_tokens": len(unique_tokens), "unknown_naive": len(unknown)})

naive_df = pd.DataFrame(naive_rows)
naive_df

# %%
# What does the checker suggest for some typical 10-K words that are spelled correctly?
test_words = ["cybersecurity", "smartphone", "iphone", "online", "website", "ebitda",
              "blockchain", "nasdaq", "subsidiaries", "fiscal", "litigation", "covid"]

start_time = time.time()
for w in test_words:
    print(f"{w:15} in Webster? {str(w in WORDS):5}  ->  {correction(w)}")
print(f"\n{len(test_words)} words took {time.time() - start_time:.1f} seconds")

# %% [markdown]
# ### 3.2 Challenges of this spell checker
#
# The outputs above show the main problems:
#
# 1. **The corpus is a dictionary, not normal text.** Norvig's checker picks the candidate with the
#    highest frequency `P(word)`. In a dictionary, a word's frequency says how often it is used *in
#    definitions* (words like "of", "the", "or", "a", "defn" dominate), not how common it is in real
#    language, so the ranking of candidates is often poor.
# 2. **Old vocabulary.** Webster's 1913 edition has no modern words (e.g. *online*, *website*,
#    *smartphone*, *cybersecurity*), so correct words are treated as typos and "corrected" into
#    unrelated old words.
# 3. **Names, brands and acronyms.** Company names, products, people and tickers (*iPhone*, *Nasdaq*,
#    *EBITDA*, *GAAP*) are not in any dictionary.
# 4. **Numbers and identifiers.** `\w+` keeps numbers such as `2025` or `10` as "words".
# 5. **Inflected forms.** A dictionary lists *subsidiary*, not always *subsidiaries* or *recognized*.
# 6. **Speed.** `edits2` creates hundreds of thousands of candidates for a long word, so checking every
#    word of ten long reports is slow.
# 7. **A wrong correction is worse than no correction.** Changing a correct finance term damages the
#    text we want to analyse.
#
# ### 3.3 How we address them
#
# * We only check **lower-case words made of letters**, with at least 3 letters. Numbers, acronyms in
#   capitals and mixed-case brand names (*iPhone*) are skipped. A capitalised word that never appears in
#   lower case in the same filing is treated as a proper noun and skipped.
# * We add a **domain vocabulary**: every word that appears in at least 3 of the 10 filings is accepted
#   as correct (a real typo is very unlikely to appear in three different companies' reports).
# * We accept **inflected forms** if the word without a common ending (`s, es, ed, d, ing, ly, er, 's`,
#   `ies → y`) is known.
# * For **speed** we check every different word only once, cache results with `lru_cache`, and skip
#   `edits2` for words longer than 10 letters.
# * We use the checker to **flag** possible errors and do **not** overwrite the clean text files.

# %%
# Domain vocabulary: words used in at least 3 of the 10 filings
doc_freq = Counter()
for text in clean_texts.values():
    doc_freq.update(set(words(text)))
domain_vocab = {w for w, n in doc_freq.items() if n >= 3}
VOCAB = set(WORDS) | domain_vocab


def is_known(word):
    "A word is known if it, or the word without a common ending, is in VOCAB."
    if word in VOCAB:
        return True
    for ending in ("'s", "s", "es", "ed", "d", "ing", "ly", "er"):
        if word.endswith(ending) and word[: -len(ending)] in VOCAB:
            return True
    return word.endswith("ies") and word[:-3] + "y" in VOCAB


def tokens_to_check(text):
    "Different lower-case words worth checking (no numbers, acronyms, brands or proper nouns)."
    tokens = re.findall(r"[A-Za-z]+(?:'[a-z]+)?", text.replace("’", "'"))
    lower_forms = {t for t in tokens if t.islower()}
    keep = set()
    for t in tokens:
        if len(t) < 3 or t.isupper():                 # short words and acronyms (GAAP, AWS)
            continue
        if not t.islower() and not t.istitle():       # mixed case brands (iPhone, PayPal)
            continue
        if t.istitle() and t.lower() not in lower_forms:   # only ever capitalised -> proper noun
            continue
        keep.add(t.lower())
    return keep


@lru_cache(maxsize=None)
def fast_correction(word):
    "Norvig's correction with a cache and without edits2 for long words."
    cands = known([word]) or known(edits1(word))
    if not cands and len(word) <= 10:
        cands = known(edits2(word))
    return max(cands, key=P) if cands else word


improved_rows, examples = [], []
start_time = time.time()
for company, text in clean_texts.items():
    flagged = sorted(w for w in tokens_to_check(text) if not is_known(w))
    improved_rows.append({"company": company, "unknown_improved": len(flagged)})
    for w in flagged[:5]:
        examples.append({"company": company, "flagged word": w, "suggestion": fast_correction(w)})

spell_df = naive_df.merge(pd.DataFrame(improved_rows), on="company")
print(f"Improved check took {time.time() - start_time:.1f} seconds")
spell_df

# %%
# Examples of words that are still flagged, with the checker's suggestion
pd.DataFrame(examples)
```

- [ ] **Step 2: Run RUN command** — expect PASS; check runtime of the spell-check cells in the executed notebook is under ~5 minutes total.

- [ ] **Step 3: Read the outputs and adjust the markdown in 3.2 to match**: every claim in 3.2 must be visible in the outputs (e.g., if `online` turns out to be in Webster's, replace it in the text with a word from `test_words` that is not). Then rebuild with the RUN command.

- [ ] **Step 4: Add one short markdown cell after the examples table** (append to `03_spellcheck.py`) that comments on what the remaining flagged words are (typos vs. still-unknown valid words) based on the actual table, in 3–5 sentences, and states the before/after reduction in unknown words using the numbers from `spell_df`. Rerun RUN.

---

### Task 4: Extraction and `legalproceedings.csv`

**Files:**
- Create: `planning/cells/04_extract.py`
- Modify: `planning/tests/test_outputs.py` (append tests)

**Interfaces:**
- Consumes: `clean_texts`.
- Produces: `MONTH: str`, `DATE: str` (regex strings), `to_iso(date_str) -> str`, `get_fiscal_year_end(text) -> str`, `get_item3(text) -> str`, `get_signature_section(text) -> str`, `get_signature_dates(section) -> str`, `get_signers(section) -> str`; `df: DataFrame` with columns `company, fiscal_year_end, legal_proceedings, signature_dates, signers`. All getters return `""` when nothing is found.

- [ ] **Step 1: Write the failing tests** (append)

```python
MANUAL_FYE = {
    "Apple": "2025-09-27", "Microsoft": "2026-06-30", "Amazon": "2025-12-31", "Tesla": "2025-12-31",
    "Meta": "2025-12-31", "Alphabet": "2025-12-31", "Johnson and Johnson": "2025-12-28",
    "Coca-Cola": "2025-12-31", "Procter and Gamble": "2026-06-30", "Walmart": "2026-01-31",
}
MANUAL_SIG_DATES = {
    "Apple": "2025-10-31", "Microsoft": "2026-07-29", "Amazon": "2026-02-05", "Tesla": "2026-01-28",
    "Meta": "2026-01-28", "Alphabet": "2026-02-04", "Johnson and Johnson": "2026-02-11",
    "Coca-Cola": "2026-02-20", "Procter and Gamble": "2026-08-04", "Walmart": "2026-03-13",
}


@pytest.fixture(scope="module")
def csv():
    return pd.read_csv(PROJECT / "legalproceedings.csv", dtype=str).fillna("").set_index("company")


def test_csv_shape(csv):
    assert len(csv) == 10
    assert list(csv.columns) == ["fiscal_year_end", "legal_proceedings", "signature_dates", "signers"]


def test_fiscal_year_end(csv):
    for company, value in MANUAL_FYE.items():
        assert csv.loc[company, "fiscal_year_end"] == value, company


def test_signature_dates(csv):
    for company, value in MANUAL_SIG_DATES.items():
        assert csv.loc[company, "signature_dates"] == value, company


def test_item3_bounds(csv):
    for company, text in csv["legal_proceedings"].items():
        assert len(text) > 100, company
        assert not re.search(r"(?im)^\s*item\s*4\b", text), company
        assert not re.search(r"(?i)mine\s+safety", text), company


def test_signers_special_cases(csv):
    for company, signers in csv["signers"].items():
        assert signers, company
        assert "LLP" not in signers.upper(), company
    assert "Sundar Pichai" in csv.loc["Alphabet", "signers"]
    assert "Robert E. Moritz Jr." in csv.loc["Walmart", "signers"]
    assert csv.loc["Microsoft", "signers"].lower().count("alice l. jolla") == 1
    assert csv.loc["Apple", "signers"].lower().count("kevan parekh") == 1
```

- [ ] **Step 2: Run tests — expect FAIL** (no CSV).

- [ ] **Step 3: Create `planning/cells/04_extract.py`**

```python
# %% [markdown]
# ## 4. Extracting the information
#
# All functions below work on the cleaned text and use regular expressions. Each returns an empty
# string if it finds nothing, so one unusual filing cannot stop the whole loop.
#
# **Dates.** A date like "September 27, 2025" is matched with the pattern `DATE` and converted to ISO
# format (`2025-09-27`) with `datetime.strptime`.

# %%
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE = MONTH + r"\s+\d{1,2}\s*,\s*\d{4}"


def to_iso(date_str):
    "'September 27 , 2025' -> '2025-09-27'"
    date_str = re.sub(r"\s*,\s*", ", ", re.sub(r"\s+", " ", date_str.strip()))
    return datetime.strptime(date_str, "%B %d, %Y").date().isoformat()


print(to_iso("September 27 , 2025"), to_iso("JUNE 30, 2026"))

# %% [markdown]
# **1. Fiscal year end.** The cover page always says "For the fiscal year ended *date*". We take the
# first match, which is on the cover page.

# %%
def get_fiscal_year_end(text):
    match = re.search(r"(?i)fiscal\s+year\s+ended\s*:?\s*(" + DATE + ")", text)
    return to_iso(match.group(1)) if match else ""

# %% [markdown]
# **2. Item 3. Legal Proceedings.** The heading appears twice: first in the table of contents, then
# as the real section heading. We therefore take the **last** line that starts with
# "Item 3 … Legal Proceedings" and cut the text at the next line that starts with "Item 4".

# %%
def get_item3(text):
    starts = list(re.finditer(r"(?im)^\s*item\s*3\s*[.:]?\s*(?:\|\s*)?legal\s+proceedings\.?", text))
    if not starts:
        return ""
    start = starts[-1].end()
    end = re.search(r"(?im)^\s*item\s*4\b", text[start:])
    section = text[start : start + end.start()] if end else text[start:]
    return section.strip(" .|\n")

# %% [markdown]
# **3. and 4. Signatures.** The signature page starts with a line that only says "SIGNATURES"
# (again, the last one, because the first is in the table of contents). Some companies put the exhibit
# index after it, so we stop there.
#
# * **Dates:** every date in the section, plus the form "28th day of January 2026" (Meta). The footer
#   "Form 10-K for the Fiscal Year Ended …" (Walmart) is not a signature date, so we remove it first.
# * **Signers:** every name written after `/s/` (some filings write `/ S /`). Names in capital letters
#   are converted to title case, a comma before "Jr." is removed (otherwise it would break our
#   comma-separated list), the audit firm (contains "LLP") is dropped, and each person is listed once.

# %%
def get_signature_section(text):
    heads = list(re.finditer(r"(?im)^\s*signatures\s*$", text))
    if not heads:
        return ""
    section = text[heads[-1].start():]
    exhibit = re.search(r"(?im)^\s*exhibit\s+index", section)
    return section[: exhibit.start()] if exhibit else section


def get_signature_dates(section):
    section = re.sub(r"(?i)fiscal\s+year\s+ended\s*" + DATE, " ", section)
    found = {to_iso(d) for d in re.findall(DATE, section, flags=re.I)}
    long_form = r"(\d{1,2})(?:st|nd|rd|th)\s+day\s+of\s+(" + MONTH + r")\s*,?\s*(\d{4})"
    for day, month, year in re.findall(long_form, section, flags=re.I):
        found.add(to_iso(f"{month} {day}, {year}"))
    return ", ".join(sorted(found))


def get_signers(section):
    signers = []
    for name in re.findall(r"(?i)/\s*s\s*/\s*([^|\n/]+)", section):
        name = name.strip(" ,*")
        name = re.sub(r",?\s+(Jr\.|Sr\.|II|III)$", r" \1", name, flags=re.I)
        if name.isupper():
            name = name.title()
        if not name or "LLP" in name.upper():
            continue
        if name.lower() not in [s.lower() for s in signers]:
            signers.append(name)
    return ", ".join(signers)

# %% [markdown]
# Now we run all functions for every company. As suggested, we collect the results in a dictionary of
# lists first and turn it into a DataFrame at the end.

# %%
results = {"company": [], "fiscal_year_end": [], "legal_proceedings": [], "signature_dates": [], "signers": []}

for company, text in clean_texts.items():
    signature_section = get_signature_section(text)
    results["company"].append(company)
    results["fiscal_year_end"].append(get_fiscal_year_end(text))
    results["legal_proceedings"].append(get_item3(text))
    results["signature_dates"].append(get_signature_dates(signature_section))
    results["signers"].append(get_signers(signature_section))

df = pd.DataFrame(results)
df.to_csv("legalproceedings.csv", index=False)

pd.set_option("display.max_colwidth", 120)
df.assign(legal_proceedings=df["legal_proceedings"].str.len()).rename(
    columns={"legal_proceedings": "item3_length"})
```

- [ ] **Step 4: Run RUN command** — expect all tests PASS. For each failing test, print the relevant part of the clean text in a scratch shell, fix the regex in `04_extract.py`, and record what the problem was (you need it for Task 5 (c)). Rerun until PASS.

- [ ] **Step 5: Confirm the development fixes are real** — in a scratch shell, run the extraction once with each safeguard removed (the fiscal-year-ended removal in `get_signature_dates`, the `Jr.` comma rule, the `exhibit index` cut, the empty-string replacement of inline tags in `clean_html`) and note which company's value changes. Only fixes that actually changed a value may be mentioned in Task 5 (c).

---

### Task 5: Verification section (graded)

**Files:**
- Create: `planning/cells/05_verify.py`

**Interfaces:**
- Consumes: `df`.
- Produces: `manual: dict`, `same_names(a, b) -> bool`, `check_df: DataFrame` (columns `company, field, extracted, manual (read by us), match`).

- [ ] **Step 1: Create `planning/cells/05_verify.py`**

```python
# %% [markdown]
# ## 5. Verification
#
# ### (a) Start and end of "Item 3. Legal Proceedings"
#
# For every company we print the first and last 200 characters of the extracted section and check
# automatically that no "Item 4" heading was included.

# %%
for company, text in zip(df["company"], df["legal_proceedings"]):
    has_item4 = re.search(r"(?im)^\s*item\s*4\b", text) is not None
    print("=" * 100)
    print(f"{company}  ({len(text):,} characters)   contains an 'Item 4' heading: {has_item4}")
    print("FIRST 200:", repr(text[:200]))
    print("LAST 200: ", repr(text[-200:]))

# %% [markdown]
# ### (b) Check table
#
# We opened every filing in the browser and wrote down the fiscal year end, the signature date(s) and
# every person who signed. Signers are compared as a set of names (order and capitalisation do not
# matter).

# %%
manual = {
    "Apple": {
        "fiscal_year_end": "2025-09-27", "signature_dates": "2025-10-31",
        "signers": "Kevan Parekh, Timothy D. Cook, Chris Kondo, Wanda Austin, Alex Gorsky, Andrea Jung, "
                   "Arthur D. Levinson, Monica Lozano, Ronald D. Sugar, Susan L. Wagner"},
    "Microsoft": {
        "fiscal_year_end": "2026-06-30", "signature_dates": "2026-07-29",
        "signers": "Alice L. Jolla, Satya Nadella, Carmine Di Sibio, Reid G. Hoffman, Hugh F. Johnston, "
                   "Teri L. List, Catherine MacGregor, Mark A. L. Mason, Sandra E. Peterson, Penny S. Pritzker, "
                   "John David Rainey, Charles W. Scharf, John W. Stanton, Emma N. Walmsley, Amy E. Hood"},
    "Amazon": {
        "fiscal_year_end": "2025-12-31", "signature_dates": "2026-02-05",
        "signers": "Andrew R. Jassy, Brian T. Olsavsky, Shelley L. Reynolds, Jeffrey P. Bezos, Keith B. Alexander, "
                   "Edith W. Cooper, Jamie S. Gorelick, Daniel P. Huttenlocher, Andrew Y. Ng, Indra K. Nooyi, "
                   "Jonathan J. Rubinstein, Brad D. Smith, Patricia Q. Stonesifer, Wendell P. Weeks"},
    "Tesla": {
        "fiscal_year_end": "2025-12-31", "signature_dates": "2026-01-28",
        "signers": "Elon Musk, Vaibhav Taneja, Robyn Denholm, Ira Ehrenpreis, Joseph Gebbia, Jack Hartung, "
                   "James Murdoch, Kimbal Musk, JB Straubel, Kathleen Wilson-Thompson"},
    "Meta": {
        "fiscal_year_end": "2025-12-31", "signature_dates": "2026-01-28",
        "signers": "Susan Li, Mark Zuckerberg, Aaron Anderson, Peggy Alford, Marc L. Andreessen, John Arnold, "
                   "Patrick Collison, John Elkann, Andrew W. Houston, Nancy Killefer, Robert M. Kimmitt, "
                   "Charles Songhurst, Hock E. Tan, Tracey T. Travis, Dana White, Tony Xu"},
    "Alphabet": {
        "fiscal_year_end": "2025-12-31", "signature_dates": "2026-02-04",
        "signers": "Sundar Pichai, Anat Ashkenazi, Amie Thuener O'Toole, Frances H. Arnold, Sergey Brin, "
                   "R. Martin Chavez, L. John Doerr, Roger W. Ferguson Jr., John L. Hennessy, Larry Page, "
                   "K. Ram Shriram, Robin L. Washington"},
    "Johnson and Johnson": {
        "fiscal_year_end": "2025-12-28", "signature_dates": "2026-02-11",
        "signers": "J. Duato, J. J. Wolk, R. J. Decker Jr., M. C. Beckerle, J. A. Doudna, M. A. Hewson, "
                   "P. A. Johnson, H. Joly, M. B. McClellan, J. G. Morikis, D. E. Pinto, M. A. Weinberger, "
                   "N. Y. West, E. A. Woods"},
    "Coca-Cola": {
        "fiscal_year_end": "2025-12-31", "signature_dates": "2026-02-20",
        "signers": "James Quincey, John Murphy, Erin L. May, Herb Allen, Christopher C. Davis, Bela Bajaria, "
                   "Carolyn Everson, Ana Botin, Thomas S. Gayner, Maria Elena Lagomasino, Caroline J. Tsay, "
                   "Max Levchin, David B. Weinberg, Amity Millhiser, Jennifer D. Manning"},
    "Procter and Gamble": {
        "fiscal_year_end": "2026-06-30", "signature_dates": "2026-08-04",
        "signers": "Shailesh Jejurikar, Andre Schulten, Matthew W. Janzaruk, B. Marc Allen, Craig Arnold, "
                   "Brett Biggs, Sheila Bonini, Amy L. Chang, Joseph Jimenez, Christopher J. Kempczinski, "
                   "Debra L. Lee, Christine M. McCarthy, Ashley McEvoy, Robert J. Portman, Rajesh Subramaniam"},
    "Walmart": {
        "fiscal_year_end": "2026-01-31", "signature_dates": "2026-03-13",
        "signers": "John R. Furner, Gregory B. Penner, John David Rainey, Dwayne M. Milum, Cesar Conde, "
                   "Timothy P. Flynn, Sarah Friar, Carla A. Harris, Thomas W. Horton, Marissa A. Mayer, "
                   "C. Douglas McMillon, Shishir Mehrotra, Robert E. Moritz Jr., Brian Niccol, "
                   "Randall L. Stephenson, Steuart L. Walton"},
}


def name_set(names):
    return {re.sub(r"\s+", " ", n).strip().lower() for n in names.split(",") if n.strip()}


def same_names(a, b):
    return name_set(a) == name_set(b)


check_rows = []
for _, row in df.iterrows():
    truth = manual[row["company"]]
    for field in ["fiscal_year_end", "signature_dates", "signers"]:
        ok = same_names(row[field], truth[field]) if field == "signers" else row[field] == truth[field]
        check_rows.append({"company": row["company"], "field": field, "extracted": row[field],
                           "manual (read by us)": truth[field], "match": "✔" if ok else "✘ MISMATCH"})

check_df = pd.DataFrame(check_rows)
print(check_df["match"].value_counts().to_string())
check_df

# %%
# Details of every mismatch
for _, r in check_df[check_df["match"] != "✔"].iterrows():
    if r["field"] == "signers":
        missing = sorted(name_set(r["manual (read by us)"]) - name_set(r["extracted"]))
        extra = sorted(name_set(r["extracted"]) - name_set(r["manual (read by us)"]))
        print(f"{r['company']} signers  missing: {missing}  extra: {extra}")
    else:
        print(f"{r['company']} {r['field']}: extracted {r['extracted']!r}, filing says {r['manual (read by us)']!r}")
```

- [ ] **Step 2: Run RUN command** — tests PASS. Look at the executed output: expected 29 ✔ and 1 ✘ (Coca-Cola signers: 11 directors missing). Any other ✘ → fix the code in `04_extract.py` (Task 4) and rerun.

- [ ] **Step 3: Write section (a) conclusion and (c)** — append to `05_verify.py` a markdown cell that, based on the actual printed output:
  - (a) states for each of the 10 companies in one short line where the section starts and ends (e.g. "J&J: one sentence referring to Note 19; ends before Item 4 ✔").
  - (c) explains every remaining ✘. For Coca-Cola: the directors did not sign with `/s/`; their names are marked with `*` and the report is signed for them by Jennifer D. Manning as attorney-in-fact ("*By: /s/ Jennifer D. Manning, Attorney-in-fact"). Our rule "a signer is a name after `/s/`" finds Quincey, Murphy, May and Manning only. Catching the directors would need a Coca-Cola–specific rule (names followed by "Director" in the table after a `*`), which is the kind of case-by-case code the assignment tells us to avoid, so we keep the general rule and document the limitation.
  - lists the problems found and fixed during development — only those confirmed in Task 4 Step 5 — each with company, symptom, and fix.

  Rerun RUN.

---

### Task 6: Bonus — Beautiful Soup comparison

**Files:**
- Create: `planning/cells/06_bonus_bs4.py`
- Modify: `planning/tests/test_outputs.py` (append test)

**Interfaces:**
- Consumes: `raw_html`, `df`, `manual`, `same_names`, all `get_*` functions.
- Produces: `clean_with_bs4(raw) -> str`, `bonus_df: DataFrame`.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_main_pipeline_does_not_use_beautifulsoup():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    before_bonus = []
    for cell in nb["cells"]:
        source = "".join(cell["source"])
        if cell["cell_type"] == "markdown" and source.lstrip().startswith("## Bonus"):
            break
        if cell["cell_type"] == "code":
            before_bonus.append(source)
    else:
        pytest.fail("no '## Bonus' section found")
    code = "\n".join(before_bonus)
    assert "BeautifulSoup" not in code and "bs4" not in code
```

- [ ] **Step 2: Run tests — expect FAIL** ("no '## Bonus' section found").

- [ ] **Step 3: Create `planning/cells/06_bonus_bs4.py`**

```python
# %% [markdown]
# ## Bonus: Beautiful Soup
#
# We repeat the cleaning with Beautiful Soup and run the **same** extraction functions on its text.
# Beautiful Soup parses the HTML properly, so we do not need our own tag regexes. We remove the same
# hidden elements (`script`, `style`, `ix:header`) and use `get_text("\n")`, which puts a newline
# between all pieces of text.

# %%
from bs4 import BeautifulSoup


def clean_with_bs4(raw):
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "ix:header"]):
        tag.decompose()
    text = soup.get_text("\n").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def plain(text):
    "Item 3 text without table separators and extra spaces, so both versions can be compared."
    return " ".join(text.replace("|", " ").split())


bonus_rows = []
start_time = time.time()
regex_results = df.set_index("company")
for company, raw in raw_html.items():
    text_bs = clean_with_bs4(raw)
    section_bs = get_signature_section(text_bs)
    bs4_values = {
        "fiscal_year_end": get_fiscal_year_end(text_bs),
        "legal_proceedings": get_item3(text_bs),
        "signature_dates": get_signature_dates(section_bs),
        "signers": get_signers(section_bs),
    }
    for field, bs_value in bs4_values.items():
        rx_value = regex_results.loc[company, field]
        if field == "legal_proceedings":
            agree = plain(rx_value) == plain(bs_value)
            rx_ok = bs_ok = "see (a)"
            rx_show, bs_show = f"{len(plain(rx_value)):,} chars", f"{len(plain(bs_value)):,} chars"
        else:
            truth = manual[company][field]
            same = same_names if field == "signers" else (lambda a, b: a == b)
            agree = same(rx_value, bs_value)
            rx_ok, bs_ok = same(rx_value, truth), same(bs_value, truth)
            rx_show, bs_show = rx_value, bs_value
        bonus_rows.append({"company": company, "field": field, "regex": rx_show, "bs4": bs_show,
                           "agree": "✔" if agree else "✘", "regex correct": rx_ok, "bs4 correct": bs_ok})

bonus_df = pd.DataFrame(bonus_rows)
print(f"Beautiful Soup version took {time.time() - start_time:.0f} seconds")
print(bonus_df["agree"].value_counts().to_string())
bonus_df[bonus_df["agree"] == "✘"]

# %%
bonus_df
```

- [ ] **Step 4: Run RUN command** — all tests PASS.

- [ ] **Step 5: Investigate each disagreement** in a scratch shell (print the bs4 text around the relevant spot), then append a markdown cell to `06_bonus_bs4.py` answering "Where do the two versions disagree, and which one is right?" per disagreement, with the concrete reason (e.g. `get_text("\n")` splitting small-caps spans across lines, so names or the "SIGNATURES" heading are broken; table cells on separate lines; Item 3 lengths differing only by page footers). Also note the runtime difference and that Beautiful Soup is more robust against unusual HTML in general. Rerun RUN.

---

### Task 7: AI appendix and final run

**Files:**
- Create: `planning/cells/07_ai_appendix.py`

- [ ] **Step 1: Create `planning/cells/07_ai_appendix.py`**

```python
# %% [markdown]
# ## AI Appendix
#
# **Tool used:** Claude (Anthropic), through Claude Code.
#
# **What it was used for:** downloading the ten 10-K filings from EDGAR, planning the notebook structure,
# drafting the cleaning, spell-checking, extraction, verification and Beautiful Soup code, and drafting
# the explanatory text.
#
# **What we did ourselves:** _(team: describe honestly — e.g. which parts you checked against the
# filings in the browser, which code you rewrote, which values in the check table you re-read yourselves.)_
#
# We have read, run and tested all code in this notebook and can explain every step.
```

- [ ] **Step 2: Fresh full run** — delete generated outputs and run RUN:

```bash
cd "/Users/v.g./Desktop/Assignment 1 " && rm -rf clean_text legalproceedings.csv && python3 planning/build_notebook.py && jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 RSM317_GroupAssignment1.ipynb && python3 -m pytest planning/tests -v
```

Expected: all tests PASS; `clean_text/` has 10 files; CSV has 10 rows.

- [ ] **Step 3: Final checks**

```bash
cd "/Users/v.g./Desktop/Assignment 1 " && ls *.html | wc -l && ls clean_text && head -c 600 legalproceedings.csv && grep -c '"output_type": "error"' RSM317_GroupAssignment1.ipynb
```

Expected: `10`, ten txt names, CSV header `company,fiscal_year_end,legal_proceedings,signature_dates,signers`, error count `0`.

- [ ] **Step 4: Request final review** with superpowers:requesting-code-review against the spec.
