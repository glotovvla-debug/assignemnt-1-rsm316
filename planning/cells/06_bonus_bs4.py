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

# %% [markdown]
# ### Where do the two versions disagree, and which one is right?
#
# Both versions agree on all fiscal-year-end dates and on most other values. Using the values we read
# in the filings as the ground truth, the 7 disagreements are:
#
# | Company / field | What happens with Beautiful Soup | Which is right |
# |---|---|---|
# | Alphabet – signers | The names are written in small capitals: `S<span>UNDAR</span> P<span>ICHAI</span>`. `get_text("\n")` puts a newline between every piece of text, so the name becomes "S", "UNDAR", "P", "ICHAI" on separate lines and only "S" is found after `/S/`. | regex |
# | Microsoft – signers and signature dates | The heading is `<span>SIGNAT</span><span>URES</span>`, which becomes "SIGNAT\nURES". Only the "Signatures" line of the table of contents matches, so the "signature section" is almost the whole report (with many exhibit dates), and the small-caps names are split as for Alphabet. | regex |
# | Walmart – Item 3 | In the text, cross-references such as *see "Item 3. Legal Proceedings"* are links (`<a>`). Because of the newline separator they now start a new line and look like a heading. The last one is in the financial statements, and no "Item 4" follows it, so the extracted section runs to the end of the report (139,663 characters). | regex |
# | Coca-Cola, Meta, Tesla – Item 3 | Same section, same start and end; the only differences are spaces where inline tags were: "$ 3.3 billion", "( In re Facebook", "Contingencies , to". | regex (cleaner text), content is the same |
#
# **Conclusion.** Beautiful Soup is the safer tool for parsing HTML in general (it handles broken
# HTML, comments and attributes correctly) and was fast here as well. But the separator in `get_text`
# matters: a newline (or space) between all text pieces breaks words that are split across tags, and
# with no separator (`get_text("")`) words from neighbouring table cells or paragraphs would be glued
# together. Our regex version avoids both problems because it treats block tags (newline), table cells
# (` | `) and inline tags (nothing) differently. For these ten filings the regex version is correct in
# every case where the two disagree.
