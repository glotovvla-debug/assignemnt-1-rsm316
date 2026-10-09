"""Re-run extraction with each safeguard removed to see which company changes (dev check, not in notebook)."""
import re
src = ""
for f in ["01_load.py", "02_clean.py", "04_extract.py"]:
    src += "\n" + open(f"planning/cells/{f}", encoding="utf-8").read()
src = re.sub(r"(?m)^print\(clean_texts\[.*$|^df\.assign.*\n.*$|^ *print\(f\"(Loaded|\{company).*$", "", src)
ns = {}; exec(src, ns)
base = ns["df"].set_index("company")

def rerun(label, patch_fn):
    n2 = dict(ns); patch_fn(n2)
    for c, t in n2["clean_texts"].items():
        sec = n2["get_signature_section"](t)
        new = {"fiscal_year_end": n2["get_fiscal_year_end"](t), "legal_proceedings": n2["get_item3"](t),
               "signature_dates": n2["get_signature_dates"](sec), "signers": n2["get_signers"](sec)}
        for k, v in new.items():
            if v != base.loc[c, k]:
                print(f"[{label}] {c} {k}: {str(v)[:150]!r}")

# 1 no fiscal-year-ended removal in signature dates
def p1(n):
    D, M, iso = n["DATE"], n["MONTH"], n["to_iso"]
    def g(section):
        found = {iso(d) for d in re.findall(D, section, flags=re.I)}
        for day, month, year in re.findall(r"(\d{1,2})(?:st|nd|rd|th)\s+day\s+of\s+(" + M + r")\s*,?\s*(\d{4})", section, flags=re.I):
            found.add(iso(f"{month} {day}, {year}"))
        return ", ".join(sorted(found))
    n["get_signature_dates"] = g
rerun("no FYE removal", p1)
# 2 no Jr comma rule
def p2(n):
    def g(section):
        out = []
        for name in re.findall(r"(?i)/\s*s\s*/\s*([^|\n/]+)", section):
            name = name.strip(" ,*")
            if name.isupper(): name = name.title()
            if not name or "LLP" in name.upper(): continue
            if name.lower() not in [s.lower() for s in out]: out.append(name)
        return ", ".join(out)
    n["get_signers"] = g
rerun("no Jr rule", p2)
# 3 no exhibit index cut
def p3(n):
    def g(text):
        heads = list(re.finditer(r"(?im)^\s*signatures\s*$", text))
        return text[heads[-1].start():] if heads else ""
    n["get_signature_section"] = g
rerun("no exhibit cut", p3)
# 4 inline tags -> space
def p4(n):
    n["clean_texts"] = {c: n["clean_html"](re.sub(r"<(span|font|b|i|a)\b", r" <\1", r)) for c, r in n["raw_html"].items()}
rerun("tags->space", p4)
# 5 first instead of last Item 3 heading
def p5(n):
    def g(text):
        starts = list(re.finditer(r"(?im)^\s*item\s*3\s*[.:]?\s*(?:\|\s*)?legal\s+proceedings\.?", text))
        if not starts: return ""
        start = starts[0].end(); end = re.search(r"(?im)^\s*item\s*4\b", text[start:])
        return (text[start:start+end.start()] if end else text[start:]).strip(" .|\n")
    n["get_item3"] = g
rerun("first Item3", p5)
# 6 no LLP filter: check if auditor in section at all
print("LLP /s/ in any signature section:", [c for c, t in ns["clean_texts"].items() if re.search(r"/s/[^|\n]*LLP", ns["get_signature_section"](t))])
print("LLP /s/ anywhere:", [c for c, t in ns["clean_texts"].items() if re.search(r"(?i)/s/[^|\n]*LLP", t)])
