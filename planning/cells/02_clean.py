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
