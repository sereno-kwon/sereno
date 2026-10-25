#!/usr/bin/env python3
"""Build the Mobility pages: one page per machine at /<slug>/index.html.

Sources
  mobility/data.json      {items: [{slug, name, maker, kind, tagline, lede, specs[[label, value]],
                                    accent, accent_dark, swatch, order, notion, edited,
                                    posts[writing slug], story[paragraph]?}]}
                          Written by the Monday sync from the Notion "Mobility" database.
  mobility/src/<slug>.md  Story body (markdown) from the Notion page body. Image placeholders
                          ![](img/<slug>-<n>.jpg) resolve to mobility/img/; unplaced images are appended.
                          Falls back to item.story paragraphs when the file is missing.
  mobility/img/<slug>-cover.jpg   Photo under the page title (optional).
  mobility/logbook.json   Public 차계부 summary from scripts/summarize_logbook.py (odometer, economy, service).
  writing/index.json      Titles for posts linked through Writing's 관련 이동수단.
Style    the <head> of scripts/post_template.html, so these pages move with Writing.
Output   <slug>/index.html for every item, and mobility/built.json (slugs built last time; folders of
         machines that disappear from data.json are removed). Generated, do not edit by hand.
"""
import html
import json
import re
import shutil
from pathlib import Path

import markdown  # pip install markdown

ROOT = Path(__file__).resolve().parent.parent
MOB = ROOT / 'mobility'
data = json.loads((MOB / 'data.json').read_text(encoding='utf-8'))
items = sorted(data['items'], key=lambda i: (i.get('order') if i.get('order') is not None else 999, i['name']))

tpl = (ROOT / 'scripts/post_template.html').read_text(encoding='utf-8')
head = tpl.split('</style>\n</head>', 1)[0] + '</style>\n'


def load_json(p, default):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default


posts_index = {p['slug']: p for p in load_json(ROOT / 'writing/index.json', [])}
logbook = load_json(MOB / 'logbook.json', {})
esc = html.escape

PAGE_CSS = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@1,700&display=swap">
<style>
  body { word-break: keep-all; overflow-wrap: anywhere; }
  .m-hero { padding-block: 72px 56px; }
  .m-hero .eyebrow { margin-bottom: 14px; }
  .m-hero h1 { font-family: "Poppins", var(--body); font-style: italic; font-weight: 700; font-size: clamp(38px, 7vw, 52px); line-height: 1.05; letter-spacing: -.015em; margin-bottom: 12px; }
  .m-hero .tagline { margin-bottom: 26px; }
  .m-hero .rule { width: 44px; height: 4px; background: var(--swatch, var(--accent)); box-shadow: inset 0 0 0 1px var(--line); margin: 0 0 26px; border-radius: 1px; }
  .m-hero .lede { max-width: 34ch; }
  .cover { margin: 0 0 72px; }
  .cover img { display: block; width: 100%; height: auto; background: var(--line); }
  .specs li { grid-template-columns: 8em 1fr; }
  .specs b { color: var(--muted); font-weight: 300; }
  .specs span { color: var(--fg); }
  @media (max-width: 440px) { .specs li { grid-template-columns: 1fr; } }
  .story .body p { max-width: 62ch; }
  .story .body h2, .story .body h3 { font-family: var(--body); font-size: 17px; font-weight: 500; text-transform: none; letter-spacing: 0; color: var(--fg); margin: 36px 0 12px; }
  .story .body h2::after, .story .body h3::after { display: none; }
  .story .body img { display: block; max-width: 100%; height: auto; margin: 28px 0; }
  .story .body blockquote { margin: 24px 0; padding-left: 16px; border-left: 1px solid var(--line); color: var(--muted); }
  .story .body ul, .story .body ol { padding-left: 1.2em; }
  .story .posts { margin-top: 28px; }
  .empty { color: var(--muted); font-size: 14px; }
  .log { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }
  .log li { display: grid; grid-template-columns: 6.5em 1fr; gap: 16px; padding-block: 14px; border-bottom: 1px solid var(--line); }
  .log time { font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; padding-top: 3px; }
  .log b { font-weight: 400; }
  .log .who { color: var(--muted); font-size: 14px; }
  .log .note { margin: 4px 0 0; font-size: 15px; }
  .log .km { color: var(--muted); font-size: 13px; font-variant-numeric: tabular-nums; }
  .log .kind { color: var(--muted); font-size: 13px; margin-right: 8px; }
  @media (max-width: 440px) { .log li { grid-template-columns: 1fr; gap: 2px; } }
  .stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); margin-bottom: 28px; }
  .stat { padding: 16px 12px 14px 0; display: grid; gap: 2px; min-width: 0; }
  .stat + .stat { border-left: 1px solid var(--line); padding-left: 16px; }
  .stat b { font-family: var(--display); font-weight: 400; font-size: 26px; line-height: 1.1; font-variant-numeric: tabular-nums; }
  .stat b small { font-family: var(--body); font-size: 12px; color: var(--muted); margin-left: 3px; }
  .stat span { font-size: 12px; color: var(--muted); letter-spacing: .04em; }
  @media (max-width: 440px) { .stats { grid-template-columns: 1fr 1fr; } .stat:nth-child(3) { grid-column: 1 / -1; border-left: 0; padding-left: 0; border-top: 1px solid var(--line); } }
  .others { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 10px 22px; }
  .others a { font-size: 14px; }
  .others a[aria-current] { color: var(--muted); border-color: transparent; pointer-events: none; }
  nav a.active::after { background: var(--accent); }
</style>
"""


def accent_css(item):
    a, d, sw = item.get('accent'), item.get('accent_dark'), item.get('swatch')
    root = []
    if a:
        root.append(f'--accent: {a};')
    if sw:
        root.append(f'--swatch: {sw};')
    if not root:
        return ''
    out = '<style>\n  :root { ' + ' '.join(root) + ' }\n'
    if a:
        d = d or a
        out += (f'  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --accent: {d}; }} }}\n'
                f'  :root[data-theme="dark"] {{ --accent: {d}; }}\n')
    return out + '</style>\n'


def ym(date):
    return (date or '')[:7].replace('-', '.')


def story_html(item):
    slug = item['slug']
    md_file = MOB / 'src' / f'{slug}.md'
    if md_file.exists():
        text = md_file.read_text(encoding='utf-8')
        m = re.match(r'^---\n.*?\n---\n?(.*)$', text, re.S)
        body = (m.group(1) if m else text).strip()
    else:
        body = '\n\n'.join(item.get('story', []))
    imgs = {int(mm.group(1)): p.name for p in (MOB / 'img').glob(f'{slug}-*.jpg')
            if (mm := re.fullmatch(rf'{re.escape(slug)}-(\d+)', p.stem))}
    used = set()

    def _ph(mm):
        n = int(mm.group(1))
        if n in imgs:
            used.add(n)
            return f'![](../mobility/img/{imgs[n]})'
        return ''
    body = re.sub(rf'!\[[^\]]*\]\((?:\.\./)?(?:mobility/)?img/{re.escape(slug)}-(\d+)[^)]*\)', _ph, body)
    extra = [imgs[n] for n in sorted(imgs) if n not in used]
    if extra:
        body = body.rstrip() + '\n\n' + '\n\n'.join(f'![](../mobility/img/{n})' for n in extra)
    if not body.strip():
        return ''
    return markdown.markdown(body, extensions=['nl2br', 'sane_lists'])


def logbook_html(slug):
    lb = logbook.get(slug)
    if not lb or not (lb.get('odometer') or lb.get('service')):
        return ''
    stats = []
    if lb.get('odometer'):
        stats.append(f'<div class="stat"><b>{lb["odometer"]:,}<small>km</small></b><span>누적 주행</span></div>')
    if lb.get('economy'):
        stats.append(f'<div class="stat"><b>{lb["economy"]}<small>km/L</small></b><span>평균 연비</span></div>')
    if lb.get('since'):
        stats.append(f'<div class="stat"><b>{ym(lb["since"])}</b><span>기록 시작</span></div>')
    parts = ['    <div class="stats">\n      ' + '\n      '.join(stats) + '\n    </div>'] if stats else []
    rows = []
    for s in lb.get('service', []):
        km = f'<span class="km"> · {s["km"]:,}km</span>' if s.get('km') else ''
        rows.append(f'      <li><time datetime="{esc(s.get("date", ""))}">{esc(ym(s.get("date")))}</time>'
                    f'<div><span class="kind">{esc(s.get("kind", ""))}</span><b>{esc(s.get("title", ""))}</b>{km}</div></li>')
    if rows:
        parts.append('    <ul class="log">\n' + '\n'.join(rows) + '\n    </ul>')
    return '  <section>\n    <h2>Logbook</h2>\n' + '\n'.join(parts) + '\n  </section>\n\n'


def render(item):
    slug = item['slug']
    nav = '\n      '.join(
        f'<a href="../{o["slug"]}/"{" class=\"active\" aria-current=\"page\"" if o["slug"] == slug else ""}>{esc(o["name"])}</a>'
        for o in items)

    cover = ''
    if (MOB / 'img' / f'{slug}-cover.jpg').exists():
        cover = f'  <figure class="cover"><img src="../mobility/img/{slug}-cover.jpg" alt="{esc(item["name"])}"></figure>\n\n'

    specs = '\n'.join(f'      <li><b>{esc(k)}</b><span>{esc(v)}</span></li>' for k, v in item.get('specs', []))

    parts = []
    body = story_html(item)
    if body:
        parts.append(f'    <div class="body">\n{body}\n    </div>')
    links = []
    for s in item.get('posts', []):
        p = posts_index.get(s)
        if p:
            links.append(f'      <li><a href="../writing/{s}.html">{esc(p["ko"]["title"])}</a>'
                         f'<time datetime="{p["date"]}">{ym(p["date"])}</time></li>')
    if links:
        parts.append('    <ul class="posts">\n' + '\n'.join(links) + '\n    </ul>')
    story = '\n'.join(parts) or '    <p class="empty">아직 쓰지 않은 이야기입니다.</p>'

    others = '\n'.join(
        f'      <li><a href="../{o["slug"]}/"{" aria-current=\"page\"" if o["slug"] == slug else ""}>{esc(o["name"])}</a></li>'
        for o in items)

    title = item['name']
    out = head.replace('[[lang]]', 'ko').replace('[[title]]', esc(title))
    out = out.replace('<meta name="viewport"',
                      f'<meta name="description" content="{esc(item.get("lede", ""))}">\n<meta name="viewport"', 1)
    out += PAGE_CSS + accent_css(item) + '</head>\n<body>\n'
    out += f"""<div class="wrap">
  <header>
    <a class="mark" href="../">SERENO</a>
    <nav aria-label="Mobility">
      {nav}
    </nav>
  </header>

  <section class="m-hero">
    <p class="eyebrow">MOBILITY · {esc(item.get('kind', ''))}</p>
    <h1>{esc(title)}</h1>
    <p class="tagline">{esc(item.get('tagline', ''))}</p>
    <div class="rule" aria-hidden="true"></div>
    <p class="lede">{esc(item.get('lede', ''))}</p>
  </section>

{cover}  <section>
    <h2>Machine</h2>
    <ul class="channels specs">
{specs}
    </ul>
  </section>

  <section class="story">
    <h2>Story</h2>
{story}
  </section>

{logbook_html(slug)}  <section>
    <h2>Mobility</h2>
    <ul class="others">
{others}
    </ul>
  </section>

  <footer>
    <span>© 2026 Sereno</span>
    <span>Seoul, KR</span>
  </footer>
</div>
<script>
  const header = document.querySelector('header');
  const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, {{ passive: true }}); onScroll();
  const active = document.querySelector('nav a.active');
  if (active) {{ const nav = active.parentElement; if (nav.scrollWidth > nav.clientWidth) nav.scrollLeft = Math.max(0, active.offsetLeft - 16); }}
</script>
</body>
</html>
"""
    return out


RESERVED = {'writing', 'photos', 'map', 'scripts', 'mobility', 'arario', 'sehee', '.git'}
built_file = MOB / 'built.json'
previous = set(load_json(built_file, []))
current = []
for item in items:
    slug = item['slug']
    if not re.fullmatch(r'[a-z0-9-]+', slug) or slug in RESERVED:
        print('skip (bad slug):', slug)
        continue
    d = ROOT / slug
    d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(render(item), encoding='utf-8')
    current.append(slug)
    print('built', f'/{slug}/')
for gone in sorted(previous - set(current)):
    d = ROOT / gone
    if gone not in RESERVED and d.is_dir() and {p.name for p in d.iterdir()} <= {'index.html'}:
        shutil.rmtree(d)
        print('removed', f'/{gone}/')
built_file.write_text(json.dumps(current) + '\n', encoding='utf-8')
