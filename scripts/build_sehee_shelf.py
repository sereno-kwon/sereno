#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draw the 서재 bookshelf for sehee/index.html and splice it into the page.

Add a title to BOOKS (in the order the books were added) and run this script:
one more volume appears on the shelf.

    python3 scripts/build_sehee_shelf.py
"""
import pathlib, re, hashlib

BOOKS = [
    "서양미술사",
]

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "sehee" / "index.html"

LINE, FG, MOSS, AMBER = "var(--line)", "var(--fg)", "var(--moss)", "var(--amber)"

# ---- case geometry ----
X0, Y0, W, H = 10, 70, 330, 384          # outer case
T = 8                                     # board thickness
SHELVES = 3
INNER_X0, INNER_X1 = X0 + T, X0 + W - T
BAY_H = (H - T * (SHELVES + 1)) / SHELVES


def bay_top(i):
    return Y0 + T + i * (BAY_H + T)


def jitter(title, lo, hi):
    h = int(hashlib.sha1(title.encode("utf-8")).hexdigest(), 16)
    return lo + (h % 1000) / 999 * (hi - lo)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


out = []

# ---- case ----
out.append(f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="2" stroke="{FG}" stroke-width="1.6"/>')
for i in range(SHELVES + 1):
    y = Y0 + i * (BAY_H + T)
    out.append(f'<rect x="{X0}" y="{y:.1f}" width="{W}" height="{T}" stroke="{FG}" stroke-width="1.1" '
               f'fill="{FG}" fill-opacity="0.05"/>')
out.append(f'<rect x="{X0}" y="{Y0}" width="{T}" height="{H}" stroke="{FG}" stroke-width="1.1" '
           f'fill="{FG}" fill-opacity="0.05"/>')
out.append(f'<rect x="{X0 + W - T}" y="{Y0}" width="{T}" height="{H}" stroke="{FG}" stroke-width="1.1" '
           f'fill="{FG}" fill-opacity="0.05"/>')
# back panel grain
for i in range(1, 6):
    x = INNER_X0 + i * (INNER_X1 - INNER_X0) / 6
    out.append(f'<line x1="{x:.1f}" y1="{Y0 + T}" x2="{x:.1f}" y2="{Y0 + H - T}" stroke="{LINE}" '
               f'stroke-width="0.4" stroke-opacity="0.5"/>')
# plinth
out.append(f'<path d="M{X0 + 6} {Y0 + H} L{X0 + 6} {Y0 + H + 12} M{X0 + W - 6} {Y0 + H} '
           f'L{X0 + W - 6} {Y0 + H + 12}" stroke="{FG}" stroke-width="1.1"/>')
out.append(f'<line x1="{X0 - 6}" y1="{Y0 + H + 12}" x2="{X0 + W + 6}" y2="{Y0 + H + 12}" '
           f'stroke="{FG}" stroke-width="1.3"/>')

# ---- books ----
cursor_bay, cursor_x = 0, INNER_X0 + 10
last = None
for n, title in enumerate(BOOKS):
    bw = jitter(title + "w", 27, 38)
    bh = BAY_H - jitter(title + "h", 6, 20)
    if cursor_x + bw > INNER_X1 - 10:
        cursor_bay, cursor_x = cursor_bay + 1, INNER_X0 + 10
        if cursor_bay >= SHELVES:
            break
    base = bay_top(cursor_bay) + BAY_H
    x, y = cursor_x, base - bh
    out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1.5" '
               f'stroke="{FG}" stroke-width="1.2" fill="{FG}" fill-opacity="0.04"/>')
    for dy in (10, 17, bh - 16, bh - 9):
        out.append(f'<line x1="{x + 4:.1f}" y1="{y + dy:.1f}" x2="{x + bw - 4:.1f}" y2="{y + dy:.1f}" '
                   f'stroke="{LINE}" stroke-width="0.8"/>')
    cx = x + bw / 2
    chars = [c for c in title if c.strip()]
    lh = 13.0
    top = y + (bh - (len(chars) - 1) * lh) / 2 + 4
    for i, ch in enumerate(chars):
        out.append(f'<text x="{cx:.1f}" y="{top + i * lh:.1f}" text-anchor="middle" font-size="10.5" '
                   f'fill="{FG}" style="font-family: var(--body)">{esc(ch)}</text>')
    last = (x, y, bw, bh)
    cursor_x += bw + 2.5

# bookmark ribbon on the most recent volume
if last:
    x, y, bw, bh = last
    out.append(f'<path d="M{x + bw - 10:.1f} {y + 3:.1f} L{x + bw - 10:.1f} {y - 11:.1f} '
               f'L{x + bw - 5:.1f} {y - 7:.1f} L{x + bw - 1:.1f} {y - 11:.1f} '
               f'L{x + bw - 1:.1f} {y + 3:.1f}" stroke="{AMBER}" stroke-width="1.2" '
               f'fill="{AMBER}" fill-opacity="0.12"/>')
    # bookend leaning against the last book
    bx = x + bw + 6
    out.append(f'<path d="M{bx:.1f} {y + bh:.1f} L{bx:.1f} {y + bh - 40:.1f}" '
               f'stroke="{FG}" stroke-width="1.6"/>')
    out.append(f'<path d="M{bx - 2:.1f} {y + bh:.1f} L{bx + 24:.1f} {y + bh:.1f}" '
               f'stroke="{FG}" stroke-width="1.6"/>')

# ---- plant on top ----
PX, PY = X0 + W - 86, Y0
out.append(f'<path d="M{PX} {PY} L{PX + 5} {PY - 26} L{PX + 39} {PY - 26} L{PX + 44} {PY} Z" '
           f'stroke="{FG}" stroke-width="1.1" fill="{FG}" fill-opacity="0.04"/>')
out.append(f'<line x1="{PX + 3}" y1="{PY - 20}" x2="{PX + 41}" y2="{PY - 20}" stroke="{LINE}" stroke-width="0.8"/>')
for dx, dy, cx_, cy_ in ((22, -26, 1, -46), (22, -26, -22, -34), (22, -26, 24, -30),
                         (22, -26, -12, -44), (22, -26, 15, -41)):
    out.append(f'<path d="M{PX + dx} {PY + dy} Q{PX + dx + cx_ * 0.5} {PY + dy + cy_ * 0.6} '
               f'{PX + dx + cx_} {PY + dy + cy_}" stroke="{MOSS}" stroke-width="1.1" '
               f'stroke-opacity="0.8"/>')
    out.append(f'<ellipse cx="{PX + dx + cx_}" cy="{PY + dy + cy_}" rx="9" ry="5.5" '
               f'transform="rotate({-28 if cx_ < 0 else 28} {PX + dx + cx_} {PY + dy + cy_})" '
               f'stroke="{MOSS}" stroke-opacity="0.7" stroke-width="1" fill="{MOSS}" fill-opacity="0.06"/>')

svg = ('<svg viewBox="0 -16 360 486" xmlns="http://www.w3.org/2000/svg" role="img" '
       'aria-label="책 한 권이 꽂힌 책장 선 드로잉" fill="none" stroke="var(--fg)" '
       'stroke-linejoin="round" stroke-linecap="round">' + "".join(out) + '</svg>')

page = PAGE.read_text(encoding="utf-8")
block = ('    <div class="shelf">' + svg +
         '\n      <p class="cap">한 권씩 늘어나는 책장</p>\n    </div>\n')
pat = re.compile(r'    <div class="shelf">.*?</div>\n', re.S)
if pat.search(page):
    page = pat.sub(block, page, count=1)
else:
    anchor = '    <div class="works">\n      <div class="pieces">\n        <article class="piece">\n          <h4>서양미술사'
    assert page.count(anchor) == 1, "anchor not found"
    page = page.replace(anchor, block + "\n" + anchor, 1)
PAGE.write_text(page, encoding="utf-8")
print(f"{len(BOOKS)} book(s) on the shelf, {len(svg)} bytes of svg")
