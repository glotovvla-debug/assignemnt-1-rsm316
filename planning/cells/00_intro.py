# %% [markdown]
# # RSM317 – Group Assignment 1: Cleaning and Parsing SEC Form 10-K Filings
#
# **Team members:**
# - Vladislav Glotov, Student ID: 1010946620
# - Ryosuke Fukui, Student ID: 1013980694
# - Andrew Ding, Student ID: 1009932218
#
# **Goal.** For the Rotman Investment Club we build a small proof-of-concept pipeline that takes the latest
# annual report (Form 10-K) of ten large US companies as plain HTML, removes the HTML tags, checks the
# spelling with Norvig's spell checker, and extracts four pieces of information from every report:
#
# 1. the fiscal year end date (ISO format),
# 2. the text of *Item 3. Legal Proceedings*,
# 3. the date(s) of the signatures (ISO format),
# 4. the people who signed the report (without the audit firm).
#
# The results are stored in `legalproceedings.csv`. In Section 5 we verify every extracted value against
# what we read in the filings ourselves. The bonus section repeats the extraction with Beautiful Soup.
#
# **Data.** The ten filings were downloaded from SEC EDGAR (company search → latest 10-K → open document)
# and saved in this folder as `<Company>_10-K.html`. They are the only HTML files in the folder.
