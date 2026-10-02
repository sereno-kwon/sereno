#!/usr/bin/env python3
"""Merge new source images into photos/ and photos/photos.json.

Usage: python3 scripts/sync_photos.py <source_dir> [--keep "stem1,stem2,..."]
- Every image in <source_dir> becomes photos/<stem>-full.jpg (max 2000px) and photos/<stem>-thumb.jpg (1200x800, 3:2 crop)
  and is added to photos.json. Existing entries are kept; an entry is replaced if its stem is in <source_dir>.
- With --keep, entries whose stem is NOT in the keep list (and not in <source_dir>) are removed along with their jpgs.
- Caption: "2026-09 남양성모성지" -> "남양성모성지"; a stem with no leading date is used whole.
- Entries are sorted by stem descending (YYYY-MM prefix puts the newest first).
"""
import json, sys, pathlib, argparse
from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener; register_heif_opener()
except ImportError:
    pass

ap = argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('--keep', default=None)
args = ap.parse_args()
src = pathlib.Path(args.source); out = pathlib.Path(__file__).resolve().parent.parent / 'photos'
out.mkdir(exist_ok=True); jf = out / 'photos.json'
entries = {e['full'][:-len('-full.jpg')]: e for e in (json.loads(jf.read_text(encoding='utf-8')) if jf.exists() else [])}

def caption(stem): return stem.split(' ', 1)[1] if ' ' in stem and stem[:4].isdigit() else stem

new = 0
for f in sorted(src.iterdir()):
    if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.heic', '.webp'): continue
    stem = f.stem
    im = ImageOps.exif_transpose(Image.open(f)).convert('RGB')
    full = im.copy(); full.thumbnail((2000, 2000)); full.save(out / f'{stem}-full.jpg', quality=85, optimize=True)
    ImageOps.fit(im, (1200, 800), Image.LANCZOS).save(out / f'{stem}-thumb.jpg', quality=82, optimize=True)
    entries[stem] = {'full': f'{stem}-full.jpg', 'thumb': f'{stem}-thumb.jpg', 'caption': caption(stem), 'w': 1200, 'h': 800}
    new += 1

removed = 0
if args.keep is not None:
    keep = {s.strip() for s in args.keep.split(',') if s.strip()} | {f.stem for f in src.iterdir()}
    for stem in list(entries):
        if stem not in keep:
            for suf in ('-full.jpg', '-thumb.jpg'): (out / f'{stem}{suf}').unlink(missing_ok=True)
            del entries[stem]; removed += 1

ordered = [entries[k] for k in sorted(entries, reverse=True)]
jf.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{new} processed, {removed} removed, {len(ordered)} total')
