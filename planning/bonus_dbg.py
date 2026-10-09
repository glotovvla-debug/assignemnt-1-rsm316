"""Dev check: where do regex and bs4 Item 3 texts differ?"""
import re, difflib
src = ""
for f in ["01_load.py", "02_clean.py", "04_extract.py"]:
    src += "\n" + open(f"planning/cells/{f}", encoding="utf-8").read()
b = open("planning/cells/06_bonus_bs4.py", encoding="utf-8").read()
src += "\n" + b[b.index("from bs4"):b.index("bonus_rows = []")]
src = re.sub(r"(?m)^print\(clean_texts\[.*$|^df\.assign.*\n.*$|^ *print\(f\"(Loaded|\{company).*$", "", src)
ns = {}; exec(src, ns)
for c in ["Coca-Cola", "Meta", "Tesla"]:
    a = ns["plain"](ns["get_item3"](ns["clean_texts"][c])).split()
    bb = ns["plain"](ns["get_item3"](ns["clean_with_bs4"](ns["raw_html"][c]))).split()
    sm = difflib.SequenceMatcher(None, a, bb, autojunk=False)
    print(c, [(" ".join(a[i1-2:i2+2]), " ".join(bb[j1-2:j2+2])) for op,i1,i2,j1,j2 in sm.get_opcodes() if op!="equal"][:6])
t = ns["clean_with_bs4"](ns["raw_html"]["Walmart"])
for m in re.finditer(r"(?i)item\s*4", t): print("WMT bs4:", repr(t[m.start()-30:m.start()+50]))
t = ns["clean_with_bs4"](ns["raw_html"]["Microsoft"])
print("MSFT sig headings bs4:", [repr(t[m.start():m.start()+25]) for m in re.finditer(r"(?im)^\s*s\s*\n?\s*ignatures", t)])
t = ns["clean_with_bs4"](ns["raw_html"]["Alphabet"]); i = t.find("/S/") if "/S/" in t else t.find("/ S /")
print("GOOG bs4:", repr(t[t.rfind("SIGNATURE")-10:][:0]), repr(t[i-5:i+60]))
print("=====")
t = ns["clean_with_bs4"](ns["raw_html"]["Walmart"])
ms = list(re.finditer(r"(?im)^\s*item\s*3\s*[.:]?\s*(?:\|\s*)?legal\s+proceedings\.?", t))
print("WMT item3 matches:", [(m.start(), repr(t[m.start()-80:m.end()+40])) for m in ms], len(t))
t = ns["clean_with_bs4"](ns["raw_html"]["Alphabet"])
sec = ns["get_signature_section"](t); print("GOOG sec:", repr(sec[1200:1500]))
t = ns["clean_with_bs4"](ns["raw_html"]["Microsoft"])
i = t.rfind("IGNATURES"); print("MSFT:", repr(t[i-10:i+20]))
