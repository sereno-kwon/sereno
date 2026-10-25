#!/usr/bin/env python3
"""Copy Mobility images from a source folder into mobility/img/, resized to max 1600px.

Usage: python3 scripts/sync_mobility_images.py <source_dir> [--force] [--keep "<comma-separated stems>"]
Source files are named <slug>-cover.<ext> (the photo under the page title) or <slug>-<n>.<ext>
(Story images, placed where the Notion page has its n-th image). They land as mobility/img/<stem>.jpg.
--keep lists every stem currently in the Drive folder; images in mobility/img/ not in that list are removed.
"""
import sys, pathlib, re
from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener; register_heif_opener()
except ImportError:
    pass

args = sys.argv[1:]
src = pathlib.Path(args[0]); force = '--force' in args
keep = None
if '--keep' in args:
    keep = {s.strip() for s in args[args.index('--keep') + 1].split(',') if s.strip()}
out = pathlib.Path(__file__).resolve().parent.parent / 'mobility' / 'img'; out.mkdir(parents=True, exist_ok=True)
n = 0
if src.exists():
    for f in sorted(src.iterdir()):
        if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.heic', '.webp'): continue
        if not re.fullmatch(r'[a-z0-9-]+-(cover|\d+)', f.stem): print('skip (name must be <slug>-cover or <slug>-<n>):', f.name); continue
        dst = out / f'{f.stem}.jpg'
        if dst.exists() and not force: continue
        im = ImageOps.exif_transpose(Image.open(f)).convert('RGB'); im.thumbnail((1600, 1600))
        im.save(dst, quality=85, optimize=True); n += 1
removed = 0
if keep is not None:
    for p in out.glob('*.jpg'):
        if p.stem not in keep: p.unlink(); removed += 1
print(f'{n} images written, {removed} removed')
