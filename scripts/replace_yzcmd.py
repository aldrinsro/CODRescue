import os
from pathlib import Path

root = Path(r"d:\ProjeWeb\CODRescue\templates")
replacements = {
    'YZ-CMD': 'COD$uite'
}

changed_files = []
for p in root.rglob('*.html'):
    try:
        text = p.read_text(encoding='utf-8')
    except Exception:
        try:
            text = p.read_text(encoding='latin-1')
        except Exception:
            print(f"Skipped (encoding): {p}")
            continue
    new_text = text
    for old, new in replacements.items():
        if old in new_text:
            new_text = new_text.replace(old, new)
    if new_text != text:
        bak = p.with_suffix(p.suffix + '.bak')
        bak.write_text(text, encoding='utf-8')
        p.write_text(new_text, encoding='utf-8')
        changed_files.append(str(p))

print(f"Replaced in {len(changed_files)} files")
for f in changed_files:
    print(f)
