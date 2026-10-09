# RSM317 Group Assignment 1 — 10-K Cleaning & Parsing Notebook: Design

Date: 2026-10-09
Source of requirements: `RSM317GroupAssignment1.pdf` (due Fri 2026-10-23, 23:59)

## Goal

A single Jupyter notebook, written at the level of a 3rd-year "Python for NLP" student, that
cleans the latest 10-K (plain HTML) of ten US companies with regex/string methods, runs Norvig's
spell checker on the result (Webster's dictionary as corpus), extracts four fields per company
into `legalproceedings.csv`, verifies every extracted value against hand-read values, and
compares against a Beautiful Soup version (bonus).

## Decisions (agreed with user)

- Include the Beautiful Soup bonus.
- Spell checker is used for **analysis only**; saved clean `.txt` files are not spell-corrected.
- Approach: one linear notebook with small helper functions and one loop over the files
  (no classes, no generic all-items splitter).
- Filings are downloaded by script from EDGAR (proper User-Agent) and saved as `.html`.

## Input filings (latest 10-K as of 2026-10-09)

| Company | Period end | Filed | EDGAR primary document |
|---|---|---|---|
| Apple | 2025-09-27 | 2025-10-31 | 320193/000032019325000079/aapl-20250927.htm |
| Microsoft | 2026-06-30 | 2026-07-29 | 789019/000119312526323660/msft-20260630.htm |
| Amazon | 2025-12-31 | 2026-02-06 | 1018724/000101872426000004/amzn-20251231.htm |
| Tesla | 2025-12-31 | 2026-01-29 | 1318605/000162828026003952/tsla-20251231.htm |
| Meta | 2025-12-31 | 2026-01-29 | 1326801/000162828026003942/meta-20251231.htm |
| Alphabet | 2025-12-31 | 2026-02-05 | 1652044/000165204426000018/goog-20251231.htm |
| Johnson & Johnson | 2025-12-28 | 2026-02-11 | 200406/000020040626000016/jnj-20251228.htm |
| Coca-Cola | 2025-12-31 | 2026-02-20 | 21344/000162828026010047/ko-20251231.htm |
| Procter & Gamble | 2026-06-30 | 2026-08-04 | 80424/000008042426000103/pg-20260630.htm |
| Walmart | 2026-01-31 | 2026-03-13 | 104169/000010416926000055/wmt-20260131.htm |

(URLs are `https://www.sec.gov/Archives/edgar/data/` + path.)

## Project folder layout (`~/Desktop/Assignment 1 /`)

```
RSM317_GroupAssignment1.ipynb
Apple_10-K.html, Microsoft_10-K.html, ...      # exactly 10 .html files, nothing else .html
clean_text/<Company>_10-K.txt                  # written by the notebook
legalproceedings.csv                           # written by the notebook
WebstersUnabridgedDictionary_pg29765(1).txt    # spell-checker corpus, found via glob("Webster*.txt")
planning/                                      # this spec + plan; not submitted
```

## Notebook structure

### 1. Setup & loading
- Imports: `re`, `html`, `pathlib.Path`, `collections.Counter`, `datetime`, `functools.lru_cache`, `pandas`.
- Loop `Path.cwd().glob("*.html")` (sorted) → dict `raw_html[company] = text`.
- Company name: regex on the inline-XBRL tag `name="dei:EntityRegistrantName"`; fallback to file stem.

### 2. Cleaning (regex + string methods only)
`clean_html(raw)`:
1. Remove `<script>`, `<style>`, `<ix:header>` blocks (hidden XBRL metadata) with content.
2. Block-level closing tags (`p`, `div`, `tr`, `li`, `h1-6`, `table`) and `<br>` → `\n`;
   cell closings (`td`, `th`) → ` | ` so table rows stay readable.
3. Remaining (inline) tags → `""` (empty, not space) — fixes small-caps spans such as
   Alphabet `S UNDAR P ICHAI` and Microsoft `B USINESS`.
4. `html.unescape`, `\xa0`/zero-width chars → normal space.
5. Collapse runs of spaces; strip each line; collapse blank lines; tidy repeated `|` separators.
Write each result to `clean_text/<Company>_10-K.txt` (UTF-8). Print character counts before/after.

Risk to check: removing inline tags without a space could glue two words together where the
only separator was a tag boundary. Verify by searching the cleaned text for the known names and
headings and by the spell-checker unknown-word list (glued words show up as unknown).

### 3. Norvig spell checker (Webster's as corpus)
- Load Webster's, cut the Gutenberg header/footer (`*** START OF` / `*** END OF`).
- Norvig's functions as published: `words`, `WORDS = Counter(...)`, `P`, `correction`,
  `candidates`, `known`, `edits1`, `edits2`.
- Naive run: unique lowercase tokens of each filing → count of tokens not in `WORDS`, sample of
  "corrections", timing on a sample.
- Challenges discussed (markdown), each tied to an example from our output:
  1. Dictionary ≠ usage frequencies (headwords appear once; definition words dominate `P`).
  2. Archaic/old vocabulary; modern terms missing (cybersecurity, smartphone, online, blockchain).
  3. Proper nouns, brand names, tickers, acronyms (iPhone, AWS, GAAP).
  4. Numbers, dates, currency, percentages.
  5. Inflections, hyphenated compounds, possessives.
  6. Speed — `edits2` produces ~n² candidates; slow on long words.
  7. Wrong "corrections" of valid words are worse than leaving them.
- Fixes implemented:
  - Tokenizer skips tokens with digits, all-caps acronyms, and tokens shorter than 3 letters.
  - Extend vocabulary with words appearing in ≥3 of the 10 filings (domain vocabulary).
  - Simple inflection check (strip `s`, `es`, `ed`, `ing`, `'s`) before flagging.
  - `@lru_cache` on `correction`; only check unique tokens.
- Show a before/after table per company (unique tokens, unknown before, unknown after) and a
  short list of remaining flagged words with suggestions. Clean text files are not modified.

### 4. Extraction
Helper functions, each taking the clean text:
- `get_fiscal_year_end(text)`: regex `fiscal year ended\s*:?\s*(Month D, YYYY)` (first match =
  cover page) → `datetime.strptime(..., "%B %d, %Y").date().isoformat()`.
- `get_item3(text)`: all matches of the heading `^Item 3.? Legal Proceedings` (case-insensitive,
  multiline, tolerant of newline between number and title); take the **last** one (the first is
  the table of contents); end at the first `^Item 4` heading after it. Return the text between.
- `get_signature_section(text)`: from the last line that is exactly `Signatures`
  (case-insensitive) to the end of the document, cut at `Exhibit Index` if it comes after.
- `get_signature_dates(section)`: all `Month D, YYYY` (and `this Dth day of Month YYYY`) dates →
  unique, ISO, comma-separated.
- `get_signers(section)`: names following `/s/` or `/ S /`; normalise case (title-case all-caps
  names), strip brackets and trailing titles; drop entries containing `LLP`; keep order, unique;
  comma-separated.
- Loop over companies → dict of lists → `pd.DataFrame` with columns
  `company, fiscal_year_end, legal_proceedings, signature_dates, signers` →
  `df.to_csv("legalproceedings.csv", index=False)`.

### 5. Verification (graded)
- (a) For each company print the first and last 200 characters of Item 3 and check
  programmatically that the text does not contain an `Item 4` heading; markdown comment per
  company that start and end are right.
- (b) `manual` dict: values read by hand from each filing (fiscal year end, signature dates,
  signers). Build a check table (extracted vs. manual) with ✔/✘ per field; ✘ highlighted.
- (c) Markdown explanation of every ✘: either the code is fixed (and the table re-run shows ✔) or
  the reason it cannot be fixed with the regex approach is explained. Known expected case:
  Coca-Cola directors signed via attorney-in-fact (`*`), not `/s/` — decide and document whether
  they count as signers.

### 6. Bonus — Beautiful Soup
- `BeautifulSoup(raw, "html.parser")`, drop `script/style/ix:header`, `get_text("\n")`, light
  whitespace tidy; reuse the same extraction functions on this text.
- Comparison table regex vs. bs4 for all four fields for all ten companies; discuss where they
  disagree (e.g. small-caps spans, table cell separation) and which is right, using the manual
  values as ground truth.

### 7. AI Appendix
States that Claude (Anthropic) was used to draft the code, analysis text, and the plan, and that
the team must verify, test, and edit it. Team to finalise the wording.

## Style constraints
- Code a 3rd-year student would write: plain functions, short docstrings/comments, f-strings,
  no classes, no type-hint-heavy code, no exotic libraries.
- Markdown cell before each code section explaining what and why.
- Relative paths only; must pass Kernel → Restart & Run All.

## Success criteria
- `jupyter nbconvert --to notebook --execute` on a fresh kernel finishes with no errors.
- 10 clean `.txt` files and `legalproceedings.csv` (10 rows) produced.
- Item 3 for all 10 contains no `Item 4` heading and starts at the real heading.
- Check table: every field ✔, or ✘ with written explanation.
- Exactly 10 `.html` files in the project folder.
