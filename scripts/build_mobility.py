#!/usr/bin/env python3
"""Build the Mobility pages: one page per machine at /<slug>/index.html.

Source:  mobility/data.json   {items: [{slug, name, maker, kind, tagline, accent, accent_dark, swatch,
                                       lede, specs[[label, value]], story[paragraph],
                                       posts[writing slug], log[{date, place, with, note}]}]}
Style:   the <head> of scripts/post_template.html, so these pages move with Writing.
Output:  <slug>/index.html for every item (generated, do not edit by hand).
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / 'mobility/data.json').read_text(encoding='utf-8'))
items = data['items']

tpl = (ROOT / 'scripts/post_template.html').read_text(encoding='utf-8')
head = tpl.split('</style>\n</head>', 1)[0] + '</style>\n'

posts_index = {}
idx_file = ROOT / 'writing/index.json'
if idx_file.exists():
    for p in json.loads(idx_file.read_text(encoding='utf-8')):
        posts_index[p['slug']] = p

esc = html.escape

PAGE_CSS = """
<style>
  body { word-break: keep-all; overflow-wrap: anywhere; }
  .m-hero { padding-block: 72px 56px; }
  .m-hero .eyebrow { margin-bottom: 14px; }
  .m-hero h1 { margin-bottom: 14px; }
  .m-hero .tagline { margin-bottom: 26px; }
  .m-hero .rule { width: 44px; height: 4px; background: var(--swatch, var(--accent)); box-shadow: inset 0 0 0 1px var(--line); margin: 0 0 26px; border-radius: 1px; }
  .m-hero .lede { max-width: 34ch; }
  .specs li { grid-template-columns: 8em 1fr; }
  .specs b { color: var(--muted); font-weight: 300; }
  .specs span { color: var(--fg); }
  @media (max-width: 440px) { .specs li { grid-template-columns: 1fr; } }
  .story p { max-width: 62ch; }
  .empty { color: var(--muted); font-size: 14px; }
  .log { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }
  .log li { display: grid; grid-template-columns: 6.5em 1fr; gap: 16px; padding-block: 14px; border-bottom: 1px solid var(--line); }
  .log time { font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; padding-top: 3px; }
  .log b { font-weight: 400; }
  .log .who { color: var(--muted); font-size: 14px; }
  .log .note { margin: 4px 0 0; font-size: 15px; }
  @media (max-width: 440px) { .log li { grid-template-columns: 1fr; gap: 2px; } }
  .others { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 10px 22px; }
  .others a { font-size: 14px; }
  .others a[aria-current] { color: var(--muted); border-color: transparent; pointer-events: none; }
  nav a.active::after { background: var(--accent); }
</style>
"""


def accent_css(item):
    a, d, sw = item.get('accent'), item.get('accent_dark'), item.get('swatch')
    if not a:
        return f'<style>\n  :root {{ --swatch: {sw}; }}\n</style>\n' if sw else ''
    d = d or a
    sw_css = f' --swatch: {sw};' if sw else ''
    return ('<style>\n'
            f'  :root {{ --accent: {a};{sw_css} }}\n'
            f'  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --accent: {d}; }} }}\n'
            f'  :root[data-theme="dark"] {{ --accent: {d}; }}\n'
            '</style>\n')


def render(item):
    slug = item['slug']
    nav = '\n      '.join(
        f'<a href="../{o["slug"]}/"{" class=\"active\" aria-current=\"page\"" if o["slug"] == slug else ""}>{esc(o["name"])}</a>'
        for o in items)

    specs = '\n'.join(
        f'      <li><b>{esc(k)}</b><span>{esc(v)}</span></li>' for k, v in item.get('specs', []))

    story_parts = [f'    <p>{esc(p)}</p>' for p in item.get('story', [])]
    links = []
    for s in item.get('posts', []):
        p = posts_index.get(s)
        if p:
            links.append(f'      <li><a href="../writing/{s}.html">{esc(p["ko"]["title"])}</a>'
                         f'<time datetime="{p["date"]}">{p["date"][:7].replace("-", ".")}</time></li>')
    if links:
        story_parts.append('    <ul class="posts">\n' + '\n'.join(links) + '\n    </ul>')
    story = '\n'.join(story_parts) or '    <p class="empty">아직 쓰지 않은 이야기입니다.</p>'

    log_items = []
    for e in sorted(item.get('log', []), key=lambda e: e.get('date', ''), reverse=True):
        date = e.get('date', '')
        who = f'<span class="who"> · {esc(e["with"])}</span>' if e.get('with') else ''
        note = f'<p class="note">{esc(e["note"])}</p>' if e.get('note') else ''
        log_items.append(f'      <li><time datetime="{esc(date)}">{esc(date[:7].replace("-", "."))}</time>'
                         f'<div><b>{esc(e.get("place", ""))}</b>{who}{note}</div></li>')
    log = ('    <ul class="log">\n' + '\n'.join(log_items) + '\n    </ul>') if log_items \
        else '    <p class="empty">첫 번째 기록을 기다리고 있습니다.</p>'

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

  <section>
    <h2>Machine</h2>
    <ul class="channels specs">
{specs}
    </ul>
  </section>

  <section class="story">
    <h2>Story</h2>
{story}
  </section>

  <section>
    <h2>Places &amp; People</h2>
{log}
  </section>

  <section>
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


for item in items:
    d = ROOT / item['slug']
    d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(render(item), encoding='utf-8')
    print('built', f"/{item['slug']}/")
