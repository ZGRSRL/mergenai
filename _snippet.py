from pathlib import Path
lines = Path('sam/document_management/app.py').read_text(encoding='utf-8').splitlines()
for idx in range(160, 340):
    print(f"{idx+1}: {lines[idx]!r}")
