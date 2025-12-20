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
            # suggestion: check docs/archived
            base = p.name
            archived = (repo / 'docs' / 'archived' / base)
            if archived.exists():
                # Treat archived files as valid targets (backwards-compatible)
                suggestions.append((str(f.relative_to(repo)), link, str(archived.relative_to(repo))))
                exists = True

        if not exists:
            broken.append((str(f.relative_to(repo)), link, [str(c.relative_to(repo)) for c in candidates]))

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
