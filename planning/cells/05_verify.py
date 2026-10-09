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
# The values in `manual` were read by hand from the cover page and the signature pages of each filing:
# the fiscal year end, the signature date(s) and every person who signed, written as printed in the
# filing. Signers are compared as a set of names: the order does not matter, but spelling, accents and
# capitalisation do.

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
                   "R. Martin Chávez, L. John Doerr, Roger W. Ferguson Jr., John L. Hennessy, Larry Page, "
                   "K. Ram Shriram, Robin L. Washington"},
    "Johnson and Johnson": {
        "fiscal_year_end": "2025-12-28", "signature_dates": "2026-02-11",
        "signers": "J. Duato, J. J. Wolk, R. J. Decker Jr., M. C. Beckerle, J. A. Doudna, M. A. Hewson, "
                   "P. A. Johnson, H. Joly, M. B. McClellan, J. G. Morikis, D. E. Pinto, M. A. Weinberger, "
                   "N. Y. West, E. A. Woods"},
    "Coca-Cola": {
        "fiscal_year_end": "2025-12-31", "signature_dates": "2026-02-20",
        "signers": "James Quincey, John Murphy, Erin L. May, Herb Allen, Christopher C. Davis, Bela Bajaria, "
                   "Carolyn Everson, Ana Botín, Thomas S. Gayner, Maria Elena Lagomasino, Caroline J. Tsay, "
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
    return {re.sub(r"\s+", " ", n).strip() for n in names.split(",") if n.strip()}


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
pd.set_option("display.max_colwidth", None)   # show the full signer lists
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

# %% [markdown]
# **Result of (a).** No section contains an "Item 4" heading, and we checked in the clean text that
# the line directly after each extracted section is the "Item 4. Mine Safety Disclosures" heading.
#
# | Company | Starts with | Ends with |
# |---|---|---|
# | Alphabet | reference to Note 10 (one sentence) | "…incorporated herein by reference." ✔ |
# | Amazon | "See Item 8 of Part II, … Note 7 …" (one sentence) | same sentence ✔ |
# | Apple | sub-heading "Digital Markets Act Investigations" | last paragraph on possible losses ✔ |
# | Coca-Cola | "The Company is involved in various legal proceedings…" | last pending case ("strong defenses to the claims.") ✔ |
# | Johnson and Johnson | reference to Note 19 (one sentence) | same sentence ✔ |
# | Meta | "As a multinational company…" | "…legal proceedings and disputes in the future." ✔ |
# | Microsoft | reference to Note 14 (one sentence) | same sentence ✔ |
# | Procter and Gamble | "The Company is subject, from time to time…" | reference to Risk Factors (Item 1A) ✔ |
# | Tesla | reference to Note 13 (one sentence) | same sentence ✔ |
# | Walmart | sub-heading "I. SUPPLEMENTAL INFORMATION" | last paragraph on possible adverse effects ✔ |
#
# Five companies only refer to a note in the financial statements; the actual case descriptions are in
# Item 8. The long sections of Coca-Cola and Meta still contain page numbers and "Table of Contents"
# lines from page breaks; these are part of the HTML text and do not change where the section starts or ends.
#
# ### (c) Explanation of the mismatches
#
# **Result:** after the fixes below, all 30 values match (30 ✔, no ✘).
#
# **Coca-Cola – signers (was a ✘ in our first version).** At first our function only found James
# Quincey, John Murphy, Erin L. May and Jennifer D. Manning, but not the 11 directors. In Coca-Cola's
# filing the directors did not sign with `/s/`: their names are marked with `*`, and Jennifer D. Manning
# signed for all of them as attorney-in-fact ("*By: /s/ JENNIFER D. MANNING … Attorney-in-fact"). We
# fixed this with a general rule (not one written only for Coca-Cola): a name at the start of a line or
# table cell that is directly followed by the title "Director" is also a signer. For the other nine
# companies this rule only finds directors who are already in the list, so their results do not change.
# A remaining limitation: an attorney-in-fact signer with a title other than "Director" in a layout like
# Coca-Cola's would still be missed.
#
# **Capitalisation of names (was hidden by our first check table).** Our first version turned capital-
# letter names with `title()` into "Macgregor", "Mccarthy", "Mcevoy" and "Chavez", and our first check
# table compared names in lower case, so it showed ✔ although the CSV was wrong. We now take the
# normally printed name from the filing (see Section 4) and compare names case-sensitively.
#
# **Problems we found and fixed while developing** (each check was re-run with the fix removed to
# confirm it matters):
#
# * **Small capitals split by tags (Alphabet, Microsoft).** When tags were replaced by a space, names
#   came out as "S Undar P Ichai" and Microsoft's "SIGNATURES" heading became "S IGNATURES", so its
#   signature section was not found and dozens of exhibit dates were reported. Fix: remove inline tags
#   without a space (Section 2). With spaces, the Item 3 text of five companies also contained extra
#   spaces inside words and before punctuation (e.g. Tesla "Contingencies , to").
# * **Table of contents (9 of 10 companies).** The first "Item 3 Legal Proceedings" match is the table
#   of contents, so the extracted "section" was just a page number. Fix: use the last match.
# * **Walmart signature date.** Each Walmart signature page has the footer "Form 10-K for the Fiscal
#   Year Ended January 31, 2026", which added 2026-01-31 as a signature date. Fix: remove "fiscal year
#   ended + date" before collecting dates.
# * **Johnson & Johnson signature dates.** J&J's exhibit index comes after the signatures and contains
#   many old dates. Fix: cut the signature section at "Exhibit index".
# * **Walmart "Robert E. Moritz, Jr.".** The comma inside the name would split one person into two
#   entries in our comma-separated list. Fix: remove the comma before "Jr.".
# * **Audit firm.** Every report contains the auditor's "/s/ … LLP" signature, but always in the
#   auditor's report, never in the Signatures section. Restricting the search to the Signatures section
#   keeps it out; the "LLP" filter is an extra safety check.
