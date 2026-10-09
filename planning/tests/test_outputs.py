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


def _cell_outputs(keyword):
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    text = ""
    for cell in nb["cells"]:
        if cell["cell_type"] == "code" and keyword in "".join(cell["source"]):
            for out in cell.get("outputs", []):
                text += "".join(out.get("text", "")) + "".join(out.get("data", {}).get("text/html", ""))
    return text


def test_signer_capitalisation(csv):
    assert "Catherine MacGregor" in csv.loc["Microsoft", "signers"]
    assert "Christine M. McCarthy" in csv.loc["Procter and Gamble", "signers"]
    assert "Ashley McEvoy" in csv.loc["Procter and Gamble", "signers"]
    assert "R. Martin Chávez" in csv.loc["Alphabet", "signers"]


def test_coca_cola_attorney_in_fact_directors(csv):
    signers = csv.loc["Coca-Cola", "signers"]
    for name in ["Herb Allen", "Christopher C. Davis", "Ana Botín", "Amity Millhiser", "Jennifer D. Manning"]:
        assert name in signers
    assert len(signers.split(", ")) == 15


def test_check_table_all_match_and_is_readable():
    out = _cell_outputs("check_rows = []")
    assert "MISMATCH" not in out
    assert "Steuart L. Walton" in out      # full signer list visible, not cut off with "..."
