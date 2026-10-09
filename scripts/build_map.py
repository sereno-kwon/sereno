#!/usr/bin/env python3
"""Build the Map section: an industry mind map whose leaves are companies, each linked to Writing posts.

Source
  map/data.json   exported from the Notion databases Industries / Companies by the sync task
                  { industries: [{slug, parent, order, name:{ko,en,ja}, desc?:{...}}],
                    companies:  [{slug, industry, order, status, ticker, url, name:{...}, tagline?:{...}, reason?:{...}, posts:[slug]}] }
  writing/index.json  (built by build_writing.py) for post titles and dates

Outputs
  map/index.html, map/en/index.html, map/ja/index.html      the mind map (SVG) + outline
  map/<company>.html, map/en/<company>.html, map/ja/<company>.html

The page chrome (fonts, colours, header) is taken from scripts/post_template.html so the section stays in step with Writing.

Usage: python3 scripts/build_map.py
"""
import json, re, pathlib, html

root = pathlib.Path(__file__).resolve().parent.parent
out = root / 'map'
data = json.loads((out / 'data.json').read_text(encoding='utf-8'))
posts_index = {p['slug']: p for p in json.loads((root / 'writing' / 'index.json').read_text(encoding='utf-8'))} if (root / 'writing' / 'index.json').exists() else {}
head = (root / 'scripts' / 'post_template.html').read_text(encoding='utf-8').split('<body>')[0]
ctpl = (root / 'scripts' / 'company_template.html').read_text(encoding='utf-8')
mtpl = (root / 'scripts' / 'map_template.html').read_text(encoding='utf-8')

LANGS = ['ko', 'en', 'ja']
UI = {
    'ko': {'map': 'Map', 'root': '관심 산업', 'lede': '지금 들여다보고 있는 산업들입니다. 가지 끝의 회사를 누르면 그 회사에 대해 쓴 글로 이어집니다.',
           'writing': 'Writing', 'no_posts': '아직 이 회사에 대해 쓴 글이 없습니다.', 'site': '홈페이지', 'ticker': '티커', 'back': '← 마인드맵', 'ko_only': '(KO)', 'outline': '목록으로 보기'},
    'en': {'map': 'Map', 'root': 'Interests', 'lede': 'The industries I am looking into. A company at the end of a branch leads to what I have written about it.',
           'writing': 'Writing', 'no_posts': 'Nothing written about this company yet.', 'site': 'Website', 'ticker': 'Ticker', 'back': '← Map', 'ko_only': '(KO)', 'outline': 'As a list'},
    'ja': {'map': 'Map', 'root': '関心領域', 'lede': 'いま見ている産業です。枝の先の会社を押すと、その会社について書いた文章につながります。',
           'writing': 'Writing', 'no_posts': 'この会社についてはまだ書いていません。', 'site': 'ウェブサイト', 'ticker': 'ティッカー', 'back': '← マップ', 'ko_only': '(KO)', 'outline': 'リストで見る'},
}
HIDDEN_STATUS = {'졸업'}

def t(d, lang):
    """pick a language from a {ko,en,ja} dict, falling back to Korean"""
    if not d: return ''
    return d.get(lang) or d.get('ko') or ''

# ---- tree -------------------------------------------------------------------------------------------------
inds = {i['slug']: dict(i, kind='industry', children=[]) for i in data['industries']}
comps = {c['slug']: dict(c, kind='company', children=[]) for c in data['companies'] if c.get('status') not in HIDDEN_STATUS}
roots = []
for i in inds.values():
    (inds[i['parent']]['children'] if i.get('parent') in inds else roots).append(i)
for c in comps.values():
    if c['industry'] in inds: inds[c['industry']]['children'].append(c)
def sort_children(n):
    n['children'].sort(key=lambda x: (x['kind'] == 'company', x.get('order') or 999, x['slug']))
    for ch in n['children']: sort_children(ch)
tree = {'kind': 'root', 'slug': '', 'children': roots}
sort_children(tree)

def path_of(c):
    out_, p = [], inds.get(c['industry'])
    while p: out_.insert(0, p); p = inds.get(p.get('parent'))
    return out_

# ---- svg layout -------------------------------------------------------------------------------------------
ROW, COL, X0, PAD = 30, 150, 16, 10
FS = 13
def text_w(s):  # rough glyph width at 13px: CJK ~ 1em, latin ~ 0.56em
    return sum(FS if ord(ch) > 0x2e7f else FS * 0.56 for ch in s)

def layout(lang):
    """assign x, y, label to every node; returns (nodes, width, height)"""
    nodes, y = [], [0]
    def label(n):
        if n['kind'] == 'root': return UI[lang]['root']
        return t(n['name'], lang)
    def place(n, depth):
        n['label'] = label(n); n['x'] = X0 + depth * COL; n['w'] = text_w(n['label'])
        if n['children']:
            for ch in n['children']: place(ch, depth + 1)
            n['y'] = (n['children'][0]['y'] + n['children'][-1]['y']) / 2
        else:
            n['y'] = ROW * (y[0] + 0.5); y[0] += 1
        nodes.append(n)
    place(tree, 0)
    width = max(n['x'] + n['w'] for n in nodes) + 24
    return nodes, width, ROW * y[0]

def svg(lang, prefix):
    nodes, W, H = layout(lang)
    parts = [f'<svg class="mindmap" viewBox="0 0 {W:.0f} {H}" width="{W:.0f}" height="{H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(UI[lang]["root"])}">']
    for n in nodes:
        for ch in n['children']:
            x1, y1 = n['x'] + n['w'] + PAD, n['y']; x2, y2 = ch['x'] - PAD, ch['y']
            mx = (x1 + x2) / 2
            parts.append(f'<path d="M{x1:.1f} {y1:.1f} C{mx:.1f} {y1:.1f} {mx:.1f} {y2:.1f} {x2:.1f} {y2:.1f}" class="edge"/>')
    for n in nodes:
        cls = n['kind']; text = html.escape(n['label'])
        el = f'<text x="{n["x"]:.1f}" y="{n["y"]:.1f}" class="node {cls}">{text}</text>'
        if cls == 'company': el = f'<a href="{prefix}{n["slug"]}.html">{el}</a>'
        parts.append(el)
    parts.append('</svg>')
    return '\n'.join(parts)

def outline(node, lang, prefix):
    items = []
    for ch in node['children']:
        if ch['kind'] == 'company':
            tick = f' <span class="ticker">{html.escape(ch["ticker"])}</span>' if ch.get('ticker') else ''
            items.append(f'<li class="company"><a href="{prefix}{ch["slug"]}.html">{html.escape(t(ch["name"], lang))}</a>{tick}</li>')
        else:
            desc = f' <span class="note">{html.escape(t(ch.get("desc"), lang))}</span>' if t(ch.get('desc'), lang) else ''
            items.append(f'<li><span class="ind">{html.escape(t(ch["name"], lang))}</span>{desc}{outline(ch, lang, prefix)}</li>')
    return '<ul class="tree">' + ''.join(items) + '</ul>' if items else ''

# ---- pages ------------------------------------------------------------------------------------------------
def switcher(lang, page):
    return '<span class="sep">/</span>'.join(
        f'<a href="{("../" if lang != "ko" else "") + ("" if L == "ko" else L + "/")}{page}" class="{"active" if L == lang else ""}">{L.upper()}</a>' for L in LANGS)

def fill(tpl, fields):
    page = head.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">') + tpl
    for k, v in fields.items(): page = page.replace('[[' + k + ']]', v)
    return page

for lang in LANGS:
    d = out if lang == 'ko' else out / lang; d.mkdir(parents=True, exist_ok=True)
    prefix = '' if lang == 'ko' else '../'
    for old in d.glob('*.html'):
        if old.stem != 'index' and old.stem not in comps: old.unlink()
    (d / 'index.html').write_text(fill(mtpl, {
        'lang': lang, 'home': prefix + '../index.html', 'lang_switch': switcher(lang, 'index.html'),
        'map_label': UI[lang]['map'], 'writing_label': UI[lang]['writing'], 'lede': UI[lang]['lede'],
        'svg': svg(lang, ''),
    }), encoding='utf-8')
    for c in comps.values():
        crumbs = ' <span class="sep">›</span> '.join(html.escape(t(p['name'], lang)) for p in path_of(c))
        meta = []
        if c.get('ticker'): meta.append(f'<li><span>{UI[lang]["ticker"]}</span>{html.escape(c["ticker"])}</li>')
        if c.get('url'):
            host = re.sub(r'^https?://(www\.)?', '', c['url']).rstrip('/')
            meta.append(f'<li><span>{UI[lang]["site"]}</span><a href="{html.escape(c["url"])}" target="_blank" rel="noopener">{html.escape(host)}</a></li>')
        related = [posts_index[s] for s in c.get('posts', []) if s in posts_index]
        related.sort(key=lambda p: p['date'], reverse=True)
        wdir = prefix + '../writing/' + ('' if lang == 'ko' else lang + '/')
        if related:
            posts_html = '<ul class="posts">' + ''.join(
                f'<li><a href="{wdir}{p["slug"]}.html">{html.escape((p.get(lang) or p["ko"])["title"])}{"" if lang == "ko" or lang in p else " " + UI[lang]["ko_only"]}</a>'
                f'<time datetime="{p["date"]}">{p["date"][:7].replace("-", ".")}</time></li>' for p in related) + '</ul>'
        else:
            posts_html = f'<p class="sample">{UI[lang]["no_posts"]}</p>'
        (d / f'{c["slug"]}.html').write_text(fill(ctpl, {
            'lang': lang, 'home': prefix + '../index.html', 'lang_switch': switcher(lang, f'{c["slug"]}.html'),
            'map_label': UI[lang]['map'], 'writing_label': UI[lang]['writing'], 'back': UI[lang]['back'],
            'title': html.escape(t(c['name'], lang)), 'crumbs': crumbs,
            'tagline_html': f'<p class="summary">{html.escape(t(c.get("tagline"), lang))}</p>' if t(c.get('tagline'), lang) else '',
            'reason_html': f'<p>{html.escape(t(c.get("reason"), lang))}</p>' if t(c.get('reason'), lang) else '',
            'meta_html': '<ul class="contact">' + ''.join(meta) + '</ul>' if meta else '',
            'posts_html': posts_html,
        }), encoding='utf-8')
print(f'{len(inds)} industries, {len(comps)} companies, {sum(len(c.get("posts", [])) for c in comps.values())} post links')
