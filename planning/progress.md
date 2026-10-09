# SDD ledger — plan: planning/2026-10-09-10k-parser-plan.md
Ruling: no git repo / no worktree — progress tracked here, RUN command replaces commits — cost if wrong: no history, low risk for a single notebook
Pre-flight: T2 consumes raw_html/current_directory (T1 produces) ok; T4 consumes clean_texts (T2) ok; T5 consumes df (T4) ok; T6 consumes raw_html, df, manual, same_names, get_* (T1,T4,T5) ok — no conflicts
Task 1: complete (tests: run.sh → 2 passed)
Task 2: complete (tests: run.sh → 4 passed; glued-word scan 0 hits)
Task 3: complete (tests: run.sh → 4 passed; markdown claims checked against outputs; Ruling: added Apple full-unknown timing cell + ing→e rule because plan's speed/inflection claims were not supported by output — cost if wrong: one extra 5s cell)
Task 4: complete (tests: run.sh → 9 passed). Ablation confirmed: FYE-removal fixes Walmart dates (2026-01-31 extra); Jr rule fixes Walmart "Moritz, Jr." comma; exhibit cut fixes J&J (dozens of exhibit dates); tags->'' fixes Alphabet+Microsoft signers, MSFT dates (SIGNATURES heading split), Item 3 of KO/Meta/Tesla/WMT/MSFT; last-not-first Item 3 needed for 9/10 (first = TOC page number). Auditor /s/ LLP in all 10 reports but outside signature section.
Task 5: complete (tests: run.sh → 9 passed; check table 29✔/1✘ Coca-Cola as planned; Ruling: get_item3 strip changed to lstrip('.')/rstrip so the last sentence keeps its period — cost if wrong: none)
Task 6: complete (tests: run.sh → 10 passed; 7 disagreements explained from evidence: GOOG/MSFT small caps, MSFT SIGNAT|URES, WMT link cross-refs, spacing KO/META/TSLA)
Task 7: complete (fresh run: 10 html, 10 txt, csv 10 rows, 0 error outputs, 10 tests passed)
Final: review by fresh opus reviewer — 0 Critical, 3 Important, 5 Minor.
Final: fixed Coca-Cola attorney-in-fact directors (general "Name\nDirector" rule) — test_coca_cola_attorney_in_fact_directors RED→GREEN, suite 13/13
Final: fixed name capitalisation (printed-name lookup, accent-insensitive) + case-sensitive check table — test_signer_capitalisation RED→GREEN, suite 13/13
Final: fixed check table truncation (max_colwidth None) — test_check_table_all_match_and_is_readable RED→GREEN, suite 13/13
Final: Ruling: re-graded minor #7 (Coca-Cola "chemical terms" claim) to Important and hedged wording — unsupported claim in graded text — cost if wrong: none
Final: Ruling: "we opened every filing in browser" reworded to "read by hand from cover/signature pages"; team placeholders left for the team to fill — only they can state their own work — cost if wrong: submission with placeholders
Final: minor (deferred): glued headings like "ITEM 3.LEGAL PROCEEDINGS" in clean txt (cosmetic)
Final: minor (deferred): some Microsoft table cells one-per-line in clean txt (cosmetic)
Final: minor (deferred): demo cells index clean_texts["Apple"] directly
