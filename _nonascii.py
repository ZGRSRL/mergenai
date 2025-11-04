from pathlib import Path
text = Path('sam/document_management/app.py').read_text(encoding='utf-8')
unique = sorted(set(ch for ch in text if ord(ch) > 127))
print(unique)
print(len(unique))
