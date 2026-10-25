#!/usr/bin/env python3
"""Turn the private 차계부 rows into the public summary the Mobility pages show.

Usage: python3 scripts/summarize_logbook.py <rows.json>

<rows.json> lives OUTSIDE the repo (e.g. /tmp/claude-0/logbook.json). It is a list of
  {"slug": "gti", "date": "YYYY-MM-DD", "kind": "주유·충전", "title": "고급휘발유 가득",
   "km": 12345, "liters": 42.1, "full": true, "amount": 98000, "place": "...", "memo": "..."}
Any field may be missing or null.

Writes mobility/logbook.json with ONLY public fields, per slug:
  {"odometer": 12345, "since": "YYYY-MM-DD", "economy": 11.8, "service": [{"date", "kind", "title", "km"}]}
amount, place and memo are never written. Fuel entries are not listed, they only feed odometer and economy.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICE = {'정비', '소모품'}
FUEL = '주유·충전'

rows = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
by = defaultdict(list)
for r in rows:
    if r.get('slug'):
        by[r['slug']].append(r)


def num(v):
    try:
        return float(v) if v not in (None, '') else None
    except (TypeError, ValueError):
        return None


def economy(entries):
    """Full-to-full average: distance between full fills / litres added after the first full fill."""
    fuel = sorted((r for r in entries if r.get('kind') == FUEL and num(r.get('km')) is not None),
                  key=lambda r: (num(r['km']), r.get('date') or ''))
    start = None
    dist = litres = 0.0
    pending = 0.0
    for r in fuel:
        l = num(r.get('liters')) or 0.0
        if start is None:
            if r.get('full'):
                start = num(r['km'])
            continue
        pending += l
        if r.get('full'):
            km = num(r['km'])
            if km > start and pending > 0:
                dist += km - start
                litres += pending
            start, pending = km, 0.0
    return round(dist / litres, 1) if litres > 0 and dist > 0 else None


out = {}
for slug, entries in sorted(by.items()):
    kms = [num(r.get('km')) for r in entries if num(r.get('km')) is not None]
    dates = sorted(r['date'] for r in entries if r.get('date'))
    service = sorted(
        ({'date': r.get('date') or '', 'kind': r['kind'], 'title': (r.get('title') or '').strip(),
          'km': int(num(r['km'])) if num(r.get('km')) is not None else None}
         for r in entries if r.get('kind') in SERVICE),
        key=lambda s: (s['date'], s['km'] or 0), reverse=True)
    out[slug] = {
        'odometer': int(max(kms)) if kms else None,
        'since': dates[0] if dates else None,
        'economy': economy(entries),
        'service': service,
    }

dst = ROOT / 'mobility' / 'logbook.json'
dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('logbook:', ', '.join(f"{k} {v['odometer'] or '-'}km, 정비 {len(v['service'])}" for k, v in out.items()) or 'empty')
