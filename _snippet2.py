from pathlib import Path
lines = Path('sam/document_management/app.py').read_text(encoding='utf-8').splitlines()
for idx,line in enumerate(lines):
    if any(ord(ch)>127 for ch in line):
        print(f"{idx+1}: {line!r}")
