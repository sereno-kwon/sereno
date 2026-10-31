#!/usr/bin/env python3
"""Build the Writing section: per-language post pages, list pages and index.json.

Sources
  writing/src/<slug>.md         Korean original (front matter: title, date, slug, summary, notion, edited)
  writing/src/en/<slug>.md      English version   (front matter adds: translated: auto | manual)
  writing/src/ja/<slug>.md      Japanese version

Outputs
  writing/<slug>.html, writing/en/<slug>.html, writing/ja/<slug>.html
  writing/index.html, writing/en/index.html, writing/ja/index.html
  writing/index.json  [{slug, date, ko:{title,summary}, en:{title,summary,translated}?, ja:{...}?}]

Images: writing/img/<slug>-<n>.jpg. Placeholders ![](img/<slug>-<n>.*) in any language's body resolve to the real file
(dropped if missing); unreferenced image files are appended at the end. Language pages use ../img/ paths.

Usage: python3 scripts/build_writing.py
"""
import json, re, pathlib, html
import markdown  # pip install markdown
import seo  # scripts/seo.py: canonical, hreflang, Open Graph, sitemap

root = pathlib.Path(__file__).resolve().parent.parent
src = root / 'writing' / 'src'; out = root / 'writing'
tpl = (root / 'scripts' / 'post_template.html').read_text(encoding='utf-8')
ltpl = (root / 'scripts' / 'list_template.html').read_text(encoding='utf-8')
out.mkdir(exist_ok=True); src.mkdir(exist_ok=True); (out / 'img').mkdir(exist_ok=True)

LANGS = ['ko', 'en', 'ja']
UI = {
    'ko': {'writing': 'Writing', 'auto': '이 글은 한국어 원문을 자동으로 번역한 것입니다.', 'ko_only': '(KO)', 'prev': '←', 'next': '→'},
    'en': {'writing': 'Writing', 'auto': 'This is an automatic translation of the Korean original.', 'ko_only': '(KO)', 'prev': '←', 'next': '→'},
    'ja': {'writing': 'Writing', 'auto': 'この記事は韓国語の原文を自動翻訳したものです。', 'ko_only': '(KO)', 'prev': '←', 'next': '→'},
}

def parse(f):
    text = f.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.S)
    meta = dict(re.findall(r'^(\w+):[ \t]*(.*)$', m.group(1), re.M)) if m else {}
    return meta, (m.group(2) if m else text)

def resolve_images(body, slug, prefix):
    imgs = {int(m.group(1)): p.name for p in (out / 'img').glob(f'{slug}-*.jpg') if (m := re.fullmatch(rf'{re.escape(slug)}-(\d+)', p.stem))}
    used = set()
    def _ph(m):
        n = int(m.group(1))
        if n in imgs: used.add(n); return f'![]({prefix}img/{imgs[n]})'
        return ''
    body = re.sub(rf'!\[[^\]]*\]\((?:\.\./)?img/{re.escape(slug)}-(\d+)[^)]*\)', _ph, body)
    extra = [imgs[n] for n in sorted(imgs) if n not in used]
    if extra: body = body.rstrip() + '\n\n' + '\n\n'.join(f'![]({prefix}img/{name})' for name in extra) + '\n'
    return body

# collect originals
posts = {}
for f in src.glob('*.md'):
    meta, body = parse(f)
    slug = meta.get('slug') or re.sub(r'[^a-z0-9-]+', '-', f.stem.lower()).strip('-')
    posts[slug] = {'slug': slug, 'date': meta.get('date', ''), 'ko': {'title': meta.get('title', f.stem), 'summary': meta.get('summary', ''), 'body': body}}
# translations
for lang in ('en', 'ja'):
    d = src / lang
    if not d.exists(): continue
    for f in d.glob('*.md'):
        meta, body = parse(f)
        slug = meta.get('slug') or f.stem
        if slug not in posts: continue
        posts[slug][lang] = {'title': meta.get('title', posts[slug]['ko']['title']), 'summary': meta.get('summary', ''), 'body': body, 'translated': meta.get('translated', 'auto')}

ordered = sorted(posts.values(), key=lambda p: p['date'], reverse=True)

def render(p, lang, prev_, next_):
    v = p.get(lang) or p['ko']; prefix = '' if lang == 'ko' else '../'
    body_md = resolve_images(v['body'], p['slug'], prefix)
    auto = (lang != 'ko' and lang in p and p[lang].get('translated') == 'auto')
    note = f'<p class="auto-note">{UI[lang]["auto"]}</p>' if auto else ''
    def link(q, arrow_left):
        if not q: return ''
        t = (q.get(lang) or q['ko'])['title']
        tag = '' if lang == 'ko' or lang in q else ' ' + UI[lang]['ko_only']
        return f'<a href="{q["slug"]}.html">{"← " if arrow_left else ""}{html.escape(t)}{tag}{"" if arrow_left else " →"}</a>'
    switcher = '<span class="sep">/</span>'.join(
        f'<a href="{("../" if lang != "ko" else "") + ("" if L == "ko" else L + "/")}{p["slug"]}.html" class="{"active" if L == lang else ""}{"" if L == "ko" or L in p else " missing"}">{L.upper()}</a>'
        for L in LANGS)
    fields = {
        'title': html.escape(v['title']),
        'date_label': p['date'].replace('-', '.') if p['date'] else '',
        'summary_html': f'<p class="summary">{html.escape(v["summary"])}</p>' if v.get('summary') else '',
        'body': note + markdown.markdown(body_md, extensions=['extra']),
        'prev_html': link(prev_, True), 'next_html': link(next_, False),
        'home': prefix + '../index.html', 'lang': lang, 'lang_switch': switcher, 'writing_label': UI[lang]['writing'],
    }
    page = tpl
    for k, val in fields.items(): page = page.replace('[[' + k + ']]', val)
    # search engines: canonical, hreflang (languages that exist), description, Open Graph, BlogPosting
    url = lambda L: f'{seo.SITE}/writing/{"" if L == "ko" else L + "/"}{p["slug"]}.html'
    alts = {L: url(L) for L in LANGS if L == 'ko' or L in p}
    first_img = re.search(r'!\[[^\]]*\]\((?:\.\./)?img/([^)\s]+)\)', body_md)
    image = f'{seo.SITE}/writing/img/{first_img.group(1)}' if first_img else None
    desc = v.get('summary') or seo.plain(markdown.markdown(v['body']))
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": v['title'], "description": desc,
          "inLanguage": lang, "mainEntityOfPage": url(lang), "author": seo.AUTHOR, "publisher": seo.AUTHOR}
    if p['date']: ld["datePublished"] = p['date']
    if image: ld["image"] = image
    page = seo.insert_after_title(page, seo.head_tags(url(lang) if lang in alts else url('ko'), f'{v["title"]} · SERENO', desc, lang, alts, image, 'article', ld))
    return page

for lang in LANGS:
    d = out if lang == 'ko' else out / lang; d.mkdir(exist_ok=True)
    # remove stale generated pages
    for old in d.glob('*.html'):
        if old.stem != 'index' and old.stem not in posts: old.unlink()
    for i, p in enumerate(ordered):
        prev_ = ordered[i + 1] if i + 1 < len(ordered) else None
        next_ = ordered[i - 1] if i > 0 else None
        (d / f'{p["slug"]}.html').write_text(render(p, lang, prev_, next_), encoding='utf-8')
    items = '\n'.join(
        f'      <li><a href="{p["slug"]}.html">{html.escape((p.get(lang) or p["ko"])["title"])}{"" if lang == "ko" or lang in p else " " + UI[lang]["ko_only"]}</a>'
        f'<time datetime="{p["date"]}">{p["date"][:7].replace("-", ".")}</time></li>' for p in ordered)
    prefix = '' if lang == 'ko' else '../'
    switcher = '<span class="sep">/</span>'.join(f'<a href="{prefix}{"" if L == "ko" else L + "/"}index.html" class="{"active" if L == lang else ""}">{L.upper()}</a>' for L in LANGS)
    page = ltpl.replace('[[items]]', items).replace('[[home]]', prefix + '../index.html').replace('[[lang]]', lang).replace('[[lang_switch]]', switcher)
    lurl = lambda L: f'{seo.SITE}/writing/{"" if L == "ko" else L + "/"}'
    ldesc = {'ko': '세레노의 글. 자전거, 일, 여행, 생각에 대한 기록.', 'en': 'Writing by Sereno: notes on bicycles, work, travel and thought.', 'ja': 'セレノの文章。自転車、仕事、旅、考えについての記録。'}[lang]
    page = seo.insert_after_title(page, seo.head_tags(lurl(lang), 'Writing · SERENO', ldesc, lang, {L: lurl(L) for L in LANGS}, None, 'website'))
    (d / 'index.html').write_text(page, encoding='utf-8')

index = []
for p in ordered:
    e = {'slug': p['slug'], 'date': p['date'], 'ko': {'title': p['ko']['title'], 'summary': p['ko']['summary']}}
    for lang in ('en', 'ja'):
        if lang in p: e[lang] = {'title': p[lang]['title'], 'summary': p[lang]['summary'], 'translated': p[lang]['translated']}
    index.append(e)
(out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(ordered)} posts; en {sum("en" in p for p in ordered)}, ja {sum("ja" in p for p in ordered)}')
seo.write_sitemap()
