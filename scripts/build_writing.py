#!/usr/bin/env python3
"""Build writing/index.json and one HTML page per post from markdown files in writing/src/.

Each markdown file starts with a front-matter block:
---
title: 남양성모성지, 마리오 보타의 콘크리트
date: 2026-09-14
slug: namyang          (optional; derived from the file name if absent)
summary: 한 줄 요약      (optional)
---
Body in markdown. Images referenced as writing/img/<file> are served as-is.

Usage: python3 scripts/build_writing.py
"""
import json, re, pathlib, html
import markdown  # pip install markdown

root = pathlib.Path(__file__).resolve().parent.parent
src = root / 'writing' / 'src'; out = root / 'writing'
tpl = (root / 'scripts' / 'post_template.html').read_text(encoding='utf-8')
out.mkdir(exist_ok=True); src.mkdir(exist_ok=True)

posts = []
for f in src.glob('*.md'):
    text = f.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.S)
    meta = dict(re.findall(r'^(\w+):\s*(.*)$', m.group(1), re.M)) if m else {}
    body = m.group(2) if m else text
    slug = meta.get('slug') or re.sub(r'[^a-z0-9-]+', '-', f.stem.lower()).strip('-')
    posts.append({'title': meta.get('title', f.stem), 'date': meta.get('date', ''), 'slug': slug,
                  'summary': meta.get('summary', ''), 'body': markdown.markdown(body, extensions=['extra'])})
posts.sort(key=lambda p: p['date'], reverse=True)

for i, p in enumerate(posts):
    prev_ = posts[i+1] if i+1 < len(posts) else None  # older
    next_ = posts[i-1] if i > 0 else None              # newer
    page = tpl.format(
        title=html.escape(p['title']),
        date_label=p['date'].replace('-', '.') if p['date'] else '',
        summary_html=f'<p class="summary">{html.escape(p["summary"])}</p>' if p['summary'] else '',
        body=p['body'],
        prev_html=f'<a href="{prev_["slug"]}.html">← {html.escape(prev_["title"])}</a>' if prev_ else '',
        next_html=f'<a href="{next_["slug"]}.html">{html.escape(next_["title"])} →</a>' if next_ else '')
    (out / f'{p["slug"]}.html').write_text(page, encoding='utf-8')

(out / 'index.json').write_text(json.dumps([{k: p[k] for k in ('title', 'date', 'slug', 'summary')} for p in posts],
                                           ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(posts)} posts')
