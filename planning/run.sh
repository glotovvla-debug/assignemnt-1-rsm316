#!/bin/bash
# Build notebook, execute on a fresh kernel, run output tests
cd "/Users/v.g./Desktop/Assignment 1 " && python3 planning/build_notebook.py && jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 RSM317_GroupAssignment1.ipynb > planning/nbconvert.log 2>&1 || { tail -30 planning/nbconvert.log; exit 1; }; python3 -m pytest planning/tests -q 2>&1 | tail -15
