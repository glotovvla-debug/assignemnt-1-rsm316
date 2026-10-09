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

# %%
# How long does the original checker need for ALL unknown words of one report (Apple)?
apple_unknown = sorted(w for w in set(words(clean_texts["Apple"])) if w not in WORDS)
start_time = time.time()
apple_corrections = {w: correction(w) for w in apple_unknown}
seconds = time.time() - start_time
changed = sum(1 for w, c in apple_corrections.items() if w != c)
print(f"{len(apple_unknown)} unknown words in Apple's 10-K, checked in {seconds:.1f} seconds; {changed} would be changed")
print("Some of them:", list(apple_corrections.items())[:15])

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
# 4. **Numbers and identifiers.** `\w+` keeps numbers as "words", and the checker happily "corrects"
#    them (`010` → `10`, `00001` → `000` in Apple's report).
# 5. **Inflected forms.** A dictionary lists base forms; many inflected forms are missing (in our
#    results e.g. *collaborating*, *amortizing*).
# 6. **Speed.** `edits2` creates hundreds of thousands of candidates for a long word. For a few words
#    this is fast, but the unknown words of one report already take several seconds (Apple above), and
#    the Investment Club's full archive (about 2 TB) would take far too long this way.
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
#   `ies → y`, `ing → e`) is known.
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
    if word.endswith("ing") and word[:-3] + "e" in VOCAB:      # collaborating -> collaborate
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

# %% [markdown]
# ### 3.4 What is left
#
# The filters and the domain vocabulary reduce the number of flagged words per report from roughly
# 700–1,300 to roughly 30–135 (table above). Looking at the remaining words, almost none of them are real
# spelling mistakes. Most are correct modern or technical words that Webster's 1913 dictionary does not
# know (*blog*, *bandwidth*, *bitcoin*, *audio*, drug names in the J&J report such as *amivantamab*),
# product names written in lower case, and pieces of web addresses (*aspx*, *atmeta*).
# The suggestions show why we do not let the checker overwrite the text: *audio* → *audit*,
# *airport* → *import*, *activism* → *actinism* and *bitcoin* → *biscotin* would all damage the report.
# Coca-Cola and J&J have the most flagged words; for J&J many of them are drug names, and Coca-Cola's
# list includes ingredient names such as *acesulfame* next to ordinary modern words (*affordability*).
# **Conclusion:** with a 1913 dictionary as corpus, Norvig's checker is useful to *flag* unusual words,
# but for professionally edited 10-K filings it should not correct them automatically. A better corpus
# would be a large collection of recent 10-K filings themselves.
