#!/usr/bin/env python3
"""Search-engine helpers shared by the build scripts (Google, Naver).

head_tags(...)     canonical, hreflang, description, Open Graph, Twitter card and JSON-LD for one page.
                   The build scripts insert the result right after </title>.
write_sitemap()    rebuilds /sitemap.xml from every published page in the repository.
                   Pages with <meta name="robots" content="noindex..."> (hidden pages, Map) and the
                   templates under scripts/ are left out automatically, so hidden pages never appear in it.

Run on its own to refresh the sitemap:  python3 scripts/seo.py
"""
import html, json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://' + (ROOT / 'CNAME').read_text(encoding='utf-8').strip()
AUTHOR = {"@type": "Person", "@id": SITE + "/#person", "name": "세레노", "alternateName": "SERENO", "url": SITE + "/"}
OG_LOCALE = {'ko': 'ko_KR', 'en': 'en_US', 'ja': 'ja_JP'}
SKIP_DIRS = {'scripts', '.git', '.github', 'src', 'figures'}


def plain(s, limit=150):
    """HTML/markdown text → one plain line for meta description."""
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', s)          # markdown images
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)      # markdown links
    s = re.sub(r'[#>*_`~|]+', ' ', s)
    s = html.unescape(re.sub(r'\s+', ' ', s)).strip()
    return s if len(s) <= limit else s[:limit - 1].rstrip() + '…'


def head_tags(url, title, desc, lang='ko', alternates=None, image=None, og_type='article', ld=None):
    """url: absolute canonical URL. alternates: {'ko': url, 'en': url, ...} (only languages that exist)."""
    e = lambda s: html.escape(s or '', quote=True)
    out = []
    if desc:
        out.append(f'<meta name="description" content="{e(desc)}">')
    out.append(f'<link rel="canonical" href="{e(url)}">')
    if alternates and len(alternates) > 1:
        for L, u in alternates.items():
            out.append(f'<link rel="alternate" hreflang="{L}" href="{e(u)}">')
        out.append(f'<link rel="alternate" hreflang="x-default" href="{e(alternates.get("ko", url))}">')
    out += [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:site_name" content="SERENO">',
        f'<meta property="og:locale" content="{OG_LOCALE.get(lang, "ko_KR")}">',
    ]
    if desc:
        out.append(f'<meta property="og:description" content="{e(desc)}">')
    if image:
        out.append(f'<meta property="og:image" content="{e(image)}">')
    out.append(f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">')
    if ld:
        out.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>')
    return '\n'.join(out) + '\n'


def insert_after_title(page, tags):
    """Put tags right after </title>, dropping any existing description (head_tags writes its own)."""
    if 'name="description"' in tags:
        page = re.sub(r'<meta name="description" content="[^"]*">\n?', '', page, count=1)
    return page.replace('</title>\n', '</title>\n' + tags, 1)


def _is_public(text):
    m = re.search(r'<meta name="robots" content="([^"]*)"', text)
    if m and 'noindex' in m.group(1):
        return False
    if 'http-equiv="refresh"' in text.lower():
        return False
    return True


def write_sitemap():
    dates = {}
    idx = ROOT / 'writing' / 'index.json'
    if idx.exists():
        dates = {p['slug']: p['date'] for p in json.loads(idx.read_text(encoding='utf-8')) if p.get('date')}
    urls = []
    for f in sorted(ROOT.rglob('*.html')):
        rel = f.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts) or f.name == '404.html':
            continue
        text = f.read_text(encoding='utf-8', errors='ignore')
        if not _is_public(text):
            continue
        path = rel.as_posix()
        path = path[:-len('index.html')] if path.endswith('index.html') else path
        urls.append((f'{SITE}/{path}', dates.get(f.stem) if path.startswith('writing/') and f.stem != 'index' else None))
    body = ''.join(
        f'  <url><loc>{html.escape(u)}</loc>' + (f'<lastmod>{d}</lastmod>' if d else '') + '</url>\n' for u, d in urls)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>\n'
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    print(f'sitemap.xml: {len(urls)} urls')


if __name__ == '__main__':
    write_sitemap()
