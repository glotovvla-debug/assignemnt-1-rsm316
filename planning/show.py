"""Print text outputs of executed notebook cells whose source contains a keyword."""
import json, sys
nb = json.load(open("RSM317_GroupAssignment1.ipynb", encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] != "code" or sys.argv[1] not in "".join(c["source"]): continue
    print(f"--- cell {i}")
    for o in c.get("outputs", []):
        if "text" in o: print("".join(o["text"])[: int(sys.argv[2]) if len(sys.argv) > 2 else 4000])
        elif "data" in o: print("".join(o["data"].get("text/plain", ""))[: int(sys.argv[2]) if len(sys.argv) > 2 else 4000])
