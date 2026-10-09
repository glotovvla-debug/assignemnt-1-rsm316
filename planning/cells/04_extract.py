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
    return section.lstrip(" .|\n").rstrip(" |\n")

# %% [markdown]
# **3. and 4. Signatures.** The signature page starts with a line that only says "SIGNATURES"
# (again, the last one, because the first is in the table of contents). Some companies put the exhibit
# index after it, so we stop there.
#
# * **Dates:** every date in the section, plus the form "28th day of January 2026" (Meta). The footer
#   "Form 10-K for the Fiscal Year Ended …" (Walmart) is not a signature date, so we remove it first.
# * **Signers:** every name written after `/s/` (some filings write `/ S /`).
#   * Many filings write the `/s/` name in capital letters and print the name normally on the next line
#     (e.g. `/s/ CHRISTINE M. MCCARTHY` and `(Christine M. McCarthy)`). We look for that printed version in
#     the section, so we get "McCarthy" instead of `title()`'s "Mccarthy". Accents are ignored when
#     comparing (`CHAVEZ` = `Chávez`).
#   * Some directors sign through an attorney-in-fact: their name is marked with `*` instead of `/s/`
#     (Coca-Cola). We therefore also take every name that starts a line (or a table cell) and is directly
#     followed by a line saying "Director".
#   * A comma before "Jr." is removed (otherwise it would break our comma-separated list), the audit firm
#     (contains "LLP") is dropped, and each person is listed only once.

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


def plain_letters(name):
    "Lower case without accents and brackets: 'Chávez' -> 'chavez', so names can be compared."
    name = unicodedata.normalize("NFKD", name.strip(" ()"))
    return "".join(ch for ch in name if not unicodedata.combining(ch)).lower()


def get_signers(section):
    names = re.findall(r"(?i)/\s*s\s*/\s*([^|\n/]+)", section)
    # directors who signed through an attorney-in-fact: "Name" followed by a line "Director"
    names += re.findall(r"(?m)(?:^|\| )([A-Z][\w.'-]*(?: [A-Z][\w.'-]*){1,3})\nDirector\b", section)
    # all lines / table cells of the section, used to find the normally printed version of a name
    cells = [c.strip(" ()") for c in re.split(r"\n|\|", section)]

    signers = []
    for name in names:
        name = name.strip(" ,*")
        name = re.sub(r",?\s+(Jr\.|Sr\.|II|III)$", r" \1", name, flags=re.I)
        if not name or "LLP" in name.upper():
            continue
        if name.isupper():
            printed = [c for c in cells if not c.isupper() and plain_letters(c) == plain_letters(name)]
            name = printed[0] if printed else name.title()
        if plain_letters(name) not in [plain_letters(s) for s in signers]:
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
