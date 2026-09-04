import os
import glob

for f in glob.glob("tests/**/*.py", recursive=True):
    with open(f, "r") as file:
        lines = file.readlines()
        
    if not lines: continue
    
    if lines[0] == "import pytest\n" and any("from __future__ import" in l for l in lines):
        # Swap lines to fix syntax
        future_idx = -1
        for i, l in enumerate(lines):
            if "from __future__ import" in l:
                future_idx = i
                break
                
        if future_idx > 0:
            lines[0], lines[future_idx] = lines[future_idx], lines[0]
            with open(f, "w") as file:
                file.writelines(lines)
