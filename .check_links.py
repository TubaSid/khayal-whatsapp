#!/usr/bin/env python3
"""Compatibility wrapper for the link checker.

Some CI runs or README examples reference ``.check_links.py`` at the
repository root. The real script lives at ``scripts/check_links.py``.
This tiny wrapper delegates execution so both invocation styles work.
"""
from __future__ import annotations

import runpy
import sys


if __name__ == "__main__":
    # Ensure the script runs as if executed directly from the repo root.
    # If the delegated script raises SystemExit, propagate it so its
    # non-zero exit code is preserved. Otherwise exit with 0.
    try:
        runpy.run_path("scripts/check_links.py", run_name="__main__")
    except SystemExit:
        raise
    else:
        sys.exit(0)
import re
from pathlib import Path

pattern = re.compile(r'\[.*?\]\((.*?)\)')
repo = Path('.').resolve()
md_files = list(repo.rglob('*.md'))
broken = []
suggestions = []

for f in md_files:
    try:
        text = f.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Could not read {f}: {e}")
        continue
    for link in pattern.findall(text):
        link = link.strip()
        if not link:
            continue
        if link.startswith(('http://','https://','mailto:')):
            continue
        if link.startswith('#'):
            continue
        # remove fragment and query
        link_path = link.split('#')[0].split('?')[0]
        # ignore links to anchors inside files like README.md#section
        p = Path(link_path)
        if p.is_absolute():
            resolved = repo / p.relative_to(p.anchor)
        else:
            resolved = (f.parent / p).resolve()
        candidates = []
        if link_path.endswith('/'):
            candidates = [resolved / 'README.md', resolved / 'index.md']
        else:
            candidates = [resolved]
        exists = any(c.exists() for c in candidates)
        if not exists:
            broken.append((str(f.relative_to(repo)), link, [str(c.relative_to(repo)) for c in candidates]))
            # suggestion: check docs/archived
            base = p.name
            archived = (repo / 'docs' / 'archived' / base)
            if archived.exists():
                suggestions.append((str(f.relative_to(repo)), link, str(archived.relative_to(repo))))

print('Checked {} markdown files.'.format(len(md_files)))
if not broken:
    print('No broken internal links found.')
else:
    print('\nBroken links found:')
    for src, link, tried in broken:
        print(f'- In {src}: link -> {link} (checked: {tried})')
    if suggestions:
        print('\nSuggestions (links that likely should point to archived files):')
        for src, link, arch in suggestions:
            print(f'- In {src}: {link} -> {arch}')

# Exit with non-zero if broken links found
if broken:
    print('\nSUMMARY: {} broken links found.'.format(len(broken)))
    raise SystemExit(2)
else:
    print('\nSUMMARY: no broken links.')
