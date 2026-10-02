#!/usr/bin/env python3
"""Copy post images from a source folder into writing/img/, resized to max 1600px.

Usage: python3 scripts/sync_writing_images.py <source_dir>
Source files are named <slug>-<n>.<ext> (e.g. north-europe-1.jpg) and land as writing/img/<slug>-<n>.jpg.
Files already present with the same stem are skipped unless --force.
"""
import sys, pathlib, re
from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener; register_heif_opener()
except ImportError:
    pass

src = pathlib.Path(sys.argv[1]); force = '--force' in sys.argv
out = pathlib.Path(__file__).resolve().parent.parent / 'writing' / 'img'; out.mkdir(parents=True, exist_ok=True)
n = 0
for f in sorted(src.iterdir()):
    if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.heic', '.webp'): continue
    if not re.fullmatch(r'[a-z0-9-]+-\d+', f.stem): print('skip (name must be <slug>-<n>):', f.name); continue
    dst = out / f'{f.stem}.jpg'
    if dst.exists() and not force: continue
    im = ImageOps.exif_transpose(Image.open(f)).convert('RGB'); im.thumbnail((1600, 1600))
    im.save(dst, quality=85, optimize=True); n += 1
print(f'{n} images written')
